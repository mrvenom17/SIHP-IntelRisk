# src/orchestrator/main.py
import asyncio
import logging
import time
import json
import hashlib
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis
import prometheus_client as prom
from prometheus_client import Counter as PrometheusCounter, Histogram
import uvicorn
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.database import get_db, create_tables
from src.core.models import (
    RawPost,
    Report,
    HumanHotspot,
    DisasterHotspot,
    CompositeHotspot,
    AggregateStatus,
    ProcessStatus,
)
from src.extractor.extractor import ExtractorA
from src.checker.checker import CheckerA as CheckerAgent, Report as CheckerReport
from src.analyser.analyser import AnalyserA as AnalyserAgent, Report as AnalyserReport
from src.detecter.detecter import DetecterA

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
INGESTED_TOTAL = PrometheusCounter('orchestrator_ingested_total', 'Raw posts ingested')
EXTRACTED_TOTAL = PrometheusCounter('orchestrator_extracted_total', 'Reports extracted')
CHECKED_TOTAL = PrometheusCounter('orchestrator_checked_total', 'Reports checked')
ANALYZED_TOTAL = PrometheusCounter('orchestrator_analyzed_total', 'Reports analyzed')
DETECTED_TOTAL = PrometheusCounter('orchestrator_detected_total', 'Composite hotspots detected')
ERRORS_TOTAL = PrometheusCounter('orchestrator_errors_total', 'Processing errors')
WORKER_LATENCY = Histogram('orchestrator_worker_latency_seconds', 'Worker processing latency', ['worker'])

# Create tables
asyncio.run(create_tables())

app = FastAPI(title="Disaster Intelligence Orchestrator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis
redis = None

@app.on_event("startup")
async def startup():
    await create_tables()
    global redis
    redis = Redis(host="localhost", port=6379, db=0, decode_responses=True)
    # Test connections
    await redis.ping()
    async with AsyncSession() as db:
        await db.execute("SELECT 1")
    logger.info("Orchestrator started successfully")

STREAMS = {
    "extract": "raw_posts",
    "check": "reports_to_check",
    "analyze": "analyzed_reports",
}

BATCH_SIZE = 20

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/ingest")
@limiter.limit("100/minute")
async def ingest(request: Request, contents: List[str], db: AsyncSession = Depends(get_db)):
    prev = await db.execute(
        select(RawPost).order_by(RawPost.timestamp.desc()).limit(1)
    )
    prev_post = prev.scalar_one_or_none()
    prev_hash = prev_post.hash if prev_post else ""
    
    for content in contents:
        h = sha256_hash(content, prev_hash)
        raw = RawPost(
            content={"text": content}, 
            hash=h, 
            prev_hash=prev_hash, 
            status=ProcessStatus.pending
        )
        db.add(raw)
        await db.commit()
        await redis.xadd(STREAMS["extract"], {"raw_post_id": str(raw.id)})
        prev_hash = h
    
    INGESTED_TOTAL.inc(len(contents))
    return {"message": f"Ingested {len(contents)} posts"}

def sha256_hash(content: str, prev_hash: str = "") -> str:
    m = hashlib.sha256()
    m.update((prev_hash + content).encode())
    return m.hexdigest()

# === Workers ===

async def extractor_worker():
    group, consumer = "extractor_group", "extractor_consumer"
    extractor = ExtractorA()
    
    while True:
        try:
            # Create consumer group
            try:
                await redis.xgroup_create(STREAMS["extract"], group, id="0", mkstream=True)
            except Exception:
                pass  # Group exists

            data = await redis.xreadgroup(
                group, consumer, {STREAMS["extract"]: ">"}, 
                count=BATCH_SIZE, block=5000
            )
            
            if not data:
                continue

            start_time = time.time()
            batch_ids = []
            batch_raws = []
            
            for stream, events in data:
                for event_id, d in events:
                    raw_post_id = int(d["raw_post_id"])
                    async with AsyncSession() as db:
                        result = await db.execute(
                            select(RawPost)
                            .where(RawPost.id == raw_post_id, RawPost.status == ProcessStatus.pending)
                            .limit(1)
                        )
                        raw = result.scalar_one_or_none()
                        if raw:
                            raw.status = ProcessStatus.processing
                            await db.commit()
                            batch_raws.append(raw)
                            batch_ids.append(event_id)

            if batch_raws:
                async with AsyncSession() as db:
                    for raw in batch_raws:
                        try:
                            result = await extractor.extract_reports(raw.content["text"])
                            if result:
                                for rep in result.reports:
                                    orm_report = Report(
                                        raw_post_id=raw.id,
                                        event_type=rep.event_type,
                                        location=rep.location,
                                        timestamp=rep.timestamp,
                                        description=rep.description,
                                        source=rep.source,
                                        confidence=rep.confidence,
                                        veracity_flag=rep.veracity_flag,
                                        media_urls=rep.media_urls or [],
                                        reporter=rep.reporter,
                                        status=ProcessStatus.pending,
                                    )
                                    db.add(orm_report)
                                    await db.flush()
                                    await db.commit()
                                    await redis.xadd(STREAMS["check"], {"report_id": str(orm_report.id)})
                            raw.status = ProcessStatus.processed
                            await db.commit()
                            EXTRACTED_TOTAL.inc()
                        except Exception as e:
                            logger.error(f"Extraction failed for raw_post_id {raw.id}: {e}")
                            raw.status = ProcessStatus.error
                            await db.commit()
                            ERRORS_TOTAL.inc()

                    for event_id in batch_ids:
                        await redis.xack(STREAMS["extract"], group, event_id)
                    
            WORKER_LATENCY.labels(worker='extractor').observe(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Extractor worker failed: {e}")
            await asyncio.sleep(5)

async def checker_worker():
    group, consumer = "checker_group", "checker_consumer"
    
    while True:
        try:
            try:
                await redis.xgroup_create(STREAMS["check"], group, id="0", mkstream=True)
            except Exception:
                pass

            data = await redis.xreadgroup(
                group, consumer, {STREAMS["check"]: ">"}, 
                count=BATCH_SIZE, block=5000
            )
            
            if not data:
                continue

            start_time = time.time()
            batch_ids = []
            batch_reports = []
            
            for stream, events in data:
                for event_id, d in events:
                    rep_id = int(d["report_id"])
                    async with AsyncSession() as db:
                        result = await db.execute(
                            select(Report)
                            .where(Report.id == rep_id, Report.status == ProcessStatus.pending)
                            .limit(1)
                        )
                        rep = result.scalar_one_or_none()
                        if rep:
                            rep.status = ProcessStatus.processing
                            await db.commit()
                            batch_reports.append(rep)
                            batch_ids.append(event_id)

            if batch_reports:
                async with AsyncSession() as db:
                    checker_reports = [
                        CheckerReport(
                            event_type=r.event_type,
                            location=r.location,
                            timestamp=r.timestamp,
                            description=r.description,
                            source=r.source,
                            media_urls=r.media_urls or [],
                            reporter=r.reporter,
                            confidence=r.confidence,
                            veracity_flag=r.veracity_flag,
                        )
                        for r in batch_reports
                    ]
                    
                    checker = CheckerAgent()
                    verified_reports = await checker.run_async(checker_reports)
                    
                    for v in verified_reports:
                        result = await db.execute(
                            select(Report)
                            .where(Report.location == v.location, Report.description == v.description)
                            .limit(1)
                        )
                        orm_report = result.scalar_one_or_none()
                        if orm_report:
                            orm_report.veracity_flag = v.veracity_flag or orm_report.veracity_flag
                            orm_report.confidence = v.confidence or orm_report.confidence
                            orm_report.status = ProcessStatus.processed
                            await db.commit()
                            await redis.xadd(STREAMS["analyze"], {"report_id": str(orm_report.id)})
                    
                    CHECKED_TOTAL.inc(len(verified_reports))
                    
                    for event_id in batch_ids:
                        await redis.xack(STREAMS["check"], group, event_id)
                        
            WORKER_LATENCY.labels(worker='checker').observe(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Checker worker failed: {e}")
            await asyncio.sleep(5)

async def analyser_worker():
    group, consumer = "analyser_group", "analyser_consumer"
    analyser = AnalyserAgent()
    
    while True:
        try:
            try:
                await redis.xgroup_create(STREAMS["analyze"], group, id="0", mkstream=True)
            except Exception:
                pass

            data = await redis.xreadgroup(
                group, consumer, {STREAMS["analyze"]: ">"}, 
                count=BATCH_SIZE, block=5000
            )
            
            if not data:
                continue

            start_time = time.time()
            batch_ids = []
            batch_reports = []
            
            for stream, events in data:
                for event_id, d in events:
                    rep_id = int(d["report_id"])
                    async with AsyncSession() as db:
                        result = await db.execute(
                            select(Report)
                            .where(Report.id == rep_id, Report.status == ProcessStatus.processed, Report.veracity_flag == "confirmed")
                            .limit(1)
                        )
                        rep = result.scalar_one_or_none()
                        if rep:
                            batch_reports.append(rep)
                            batch_ids.append(event_id)

            if batch_reports:
                async with AsyncSession() as db:
                    for rep in batch_reports:
                        pydantic_report = AnalyserReport(
                            event_type=rep.event_type,
                            location=rep.location,
                            timestamp=rep.timestamp.isoformat() if rep.timestamp else None,
                            description=rep.description,
                            source=rep.source,
                            confidence=rep.confidence,
                        )
                        analysis = await analyser.analyze_reports_async([pydantic_report])
                        
                        for h in analysis.human_hotspots:
                            obj = HumanHotspot(
                                report_id=rep.id,
                                location=h.location,
                                timestamp=h.timestamp,
                                emotions=[em.dict() for em in h.emotions],
                                panic_level=h.panic_level,
                                confidence=0.8,
                                status=AggregateStatus.pending,
                            )
                            db.add(obj)
                        
                        for d in analysis.disaster_hotspots:
                            obj = DisasterHotspot(
                                report_id=rep.id,
                                location=d.location,
                                timestamp=d.timestamp,
                                event_type=d.event_type,
                                severity=d.severity,
                                risk_level=d.risk_level,
                                confidence=0.9,
                                status=AggregateStatus.pending,
                            )
                            db.add(obj)
                    
                    await db.commit()
                    ANALYZED_TOTAL.inc(len(batch_reports))
                    
                    for event_id in batch_ids:
                        await redis.xack(STREAMS["analyze"], group, event_id)
                        
            WORKER_LATENCY.labels(worker='analyser').observe(time.time() - start_time)
            
        except Exception as e:
            logger.error(f"Analyser worker failed: {e}")
            await asyncio.sleep(5)

async def detection_scheduler():
    while True:
        try:
            async with AsyncSession() as db:
                humans = await db.execute(
                    select(HumanHotspot).where(HumanHotspot.status == AggregateStatus.pending)
                )
                disasters = await db.execute(
                    select(DisasterHotspot).where(DisasterHotspot.status == AggregateStatus.pending)
                )
                human_list = humans.scalars().all()
                disaster_list = disasters.scalars().all()

                if not human_list and not disaster_list:
                    await asyncio.sleep(60)
                    continue

                detecter = DetecterA(db)
                composite_hotspots = await detecter.generate_map_json_with_persistence()

                for h in human_list:
                    h.status = AggregateStatus.aggregated
                for d in disaster_list:
                    d.status = AggregateStatus.aggregated

                await db.commit()
                DETECTED_TOTAL.inc(len(composite_hotspots))
                
            await asyncio.sleep(300)  # Run every 5 minutes
            
        except Exception as e:
            logger.error(f"Detection scheduler failed: {e}")
            await asyncio.sleep(60)

# === API Endpoints ===

@app.get("/api/map/latest")
async def get_map(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompositeHotspot)
        .order_by(CompositeHotspot.created_at.desc())
        .limit(100)
    )
    hotspots = result.scalars().all()
    
    if not hotspots:
        raise HTTPException(status_code=404, detail="No map data available")
    
    return {
        "hotspots": [
            {
                "latitude": h.latitude,
                "longitude": h.longitude,
                "aggregated_emotions": h.aggregated_emotions,
                "average_panic_level": h.average_panic_level,
                "event_types": h.event_types,
                "severity_level": h.severity_level,
                "risk_level": h.risk_level,
                "contributing_reports": h.contributing_reports_count,
            }
            for h in hotspots
        ]
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return Response(prom.generate_latest(), media_type="text/plain; version=0.0.4")

# === Startup ===

@app.on_event("startup")
async def start_workers():
    asyncio.create_task(extractor_worker())
    asyncio.create_task(checker_worker())
    asyncio.create_task(analyser_worker())
    asyncio.create_task(detection_scheduler())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)