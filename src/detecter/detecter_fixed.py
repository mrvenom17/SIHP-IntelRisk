# src/detecter/detecter_fixed.py
import asyncio
import logging
import math
import time
import requests
from typing import List, Optional, Dict, Any, Tuple
from prometheus_client import Histogram, Gauge, Counter as PrometheusCounter
from collections import defaultdict, Counter
from datetime import datetime
from functools import lru_cache
import numpy as np
from sklearn.cluster import DBSCAN
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
GEOCODING_REQUESTS = PrometheusCounter(
    'detecter_geocoding_requests_total',
    documentation='Number of geocoding requests made to Nominatim',
    labelnames=[]
)

GEOCODING_ERRORS = PrometheusCounter(
    'detecter_geocoding_errors_total',
    documentation='Geocoding errors',
    labelnames=[]
)

CLUSTERS_CREATED = PrometheusCounter(
    'detecter_clusters_created_total',
    documentation='Clusters created',
    labelnames=[]
)

COMPOSITE_HOTSPOTS_UPDATED = PrometheusCounter(
    'detecter_composite_hotspots_updated_total',
    documentation='Composite hotspots updated',
    labelnames=[]
)

COMPOSITE_HOTSPOTS_CREATED = PrometheusCounter(
    'detecter_composite_hotspots_created_total',
    documentation='Composite hotspots created',
    labelnames=[]
)

PROCESSING_DURATION = Histogram(
    'detecter_processing_duration_seconds',
    documentation='Time spent generating map',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# === 1. Pydantic Schemas (for output) ===

class CompositeHotspotOutput(BaseModel):
    latitude: float
    longitude: float
    aggregated_emotions: Dict[str, float]
    average_panic_level: float
    event_types: List[str]
    severity_level: str
    risk_level: str
    contributing_reports: int

# === 2. GeoCoder with LRU Cache and Precise Rate Limiting ===

class GeoCoder:
    def __init__(self, user_agent: str = "disaster-intel-agent/1.0"):
        self.user_agent = user_agent
        self.last_call_time = 0.0

    @lru_cache(maxsize=1000)
    def geocode(self, location: str) -> Optional[Tuple[float, float]]:
        if not location or not location.strip():
            return None

        # Nominatim rate limit: 1 request per second
        now = time.time()
        if now - self.last_call_time < 1:
            time.sleep(1 - (now - self.last_call_time))  # FIXED: Use time.sleep instead of await
        self.last_call_time = now

        GEOCODING_REQUESTS.inc()

        url = "https://nominatim.openstreetmap.org/search"  # FIXED: removed trailing spaces
        params = {"q": location, "format": "json", "limit": 1}
        headers = {"User-Agent": self.user_agent}

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
        except Exception as e:
            logger.error(f"Geocoding error for '{location}': {e}")
            GEOCODING_ERRORS.inc()
            return None

# === 3. Haversine Distance ===

def haversine_distance(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, c1)
    lat2, lon2 = map(math.radians, c2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Earth radius in km
    return c * r

# === 4. DetecterA (Async) ===

class DetecterA:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.geocoder = GeoCoder()

    async def assemble_unified_points(self, human_hotspots, disaster_hotspots) -> List[Dict]:
        points = []
        tasks = []

        for h in human_hotspots:
            tasks.append(self._process_hotspot("human", h))
        for d in disaster_hotspots:
            tasks.append(self._process_hotspot("disaster", d))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Hotspot processing failed: {result}")
                continue
            if result:
                points.append(result)
        return points

    async def _process_hotspot(self, hotspot_type: str, hotspot) -> Optional[Dict]:
        coords = self.geocoder.geocode(hotspot.location or "")
        if not coords:
            return None
        return {
            "type": hotspot_type,
            "payload": hotspot,
            "latitude": coords[0],
            "longitude": coords[1],
            "confidence": getattr(hotspot, "confidence", 1.0) or 1.0,
        }

    def cluster_points(self, points: List[Dict]) -> Dict[int, List[Dict]]:
        if not points:
            return {}

        coords = [(p["latitude"], p["longitude"]) for p in points]
        radians_coords = [(math.radians(lat), math.radians(lon)) for lat, lon in coords]
        X = np.array(radians_coords)
        clustering = DBSCAN(eps=5.0 / 6371.0, min_samples=1, metric="haversine").fit(X)

        clusters = defaultdict(list)
        for label, point in zip(clustering.labels_, points):
            clusters[label].append(point)
        return clusters

    async def update_or_create_composite_hotspot(self, cluster_points: List[Dict]) -> Dict:
        total_confidence = sum(p["confidence"] for p in cluster_points)
        if total_confidence == 0:
            total_confidence = 1.0

        avg_lat = sum(p["latitude"] * p["confidence"] for p in cluster_points) / total_confidence
        avg_lon = sum(p["longitude"] * p["confidence"] for p in cluster_points) / total_confidence

        # Query existing within 5km
        from core.models import CompositeHotspot  # Import here to avoid circular
        approx_deg = 0.05  # ~5.5km at equator
        stmt = select(CompositeHotspot).where(
            CompositeHotspot.latitude.between(avg_lat - approx_deg, avg_lat + approx_deg),
            CompositeHotspot.longitude.between(avg_lon - approx_deg, avg_lon + approx_deg),
        )
        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        existing = None
        for ch in candidates:
            dist = haversine_distance((ch.latitude, ch.longitude), (avg_lat, avg_lon))
            if dist <= 5.0:
                existing = ch
                break

        # Aggregate data
        emotion_agg = defaultdict(float)
        panic_scores = []
        severity_scale = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        risk_counts = Counter()
        event_types_set = set()
        severity_vals = []
        report_ids = set()

        for p in cluster_points:
            payload = p["payload"]
            report_id = getattr(payload, "report_id", None)
            if report_id:
                report_ids.add(report_id)

            if p["type"] == "human":
                emotions = getattr(payload, "emotions", []) or []
                for emo in emotions:
                    emotion_agg[emo["emotion"]] += emo["score"] * p["confidence"]
                panic_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
                panic_level = (getattr(payload, "panic_level", "") or "").lower()
                panic_scores.append(p["confidence"] * panic_map.get(panic_level, 0.0))
            elif p["type"] == "disaster":
                event_type = getattr(payload, "event_type", None)
                if event_type:
                    event_types_set.add(event_type)
                severity = getattr(payload, "severity", "low")
                sev_val = severity_scale.get(severity, 1)
                severity_vals.append(sev_val * p["confidence"])
                risk_level = getattr(payload, "risk_level", None)
                if risk_level:
                    risk_counts[risk_level] += 1

        total_reports = (existing.contributing_reports_count if existing else 0) + len(report_ids)
        rev_severity = {v: k for k, v in severity_scale.items()}

        if existing:
            # Update existing
            COMPOSITE_HOTSPOTS_UPDATED.inc()
            aggregated_emotions = existing.aggregated_emotions or {}
            for emo, score in emotion_agg.items():
                prev_score = aggregated_emotions.get(emo, 0.0)
                new_score = (prev_score * existing.contributing_reports_count + score) / total_reports
                aggregated_emotions[emo] = new_score

            avg_panic = (
                (existing.average_panic_level or 0) * existing.contributing_reports_count + sum(panic_scores)
            ) / total_reports

            event_types = list(set((existing.event_types or []) + list(event_types_set)))
            severity_level_num = max([severity_scale.get(existing.severity_level, 1)] + severity_vals or [1])
            severity_level = rev_severity.get(severity_level_num, "low")
            risk_level = risk_counts.most_common(1)[0][0] if risk_counts else existing.risk_level

            # Weighted centroid
            new_lat = (existing.latitude * existing.contributing_reports_count + avg_lat * len(report_ids)) / total_reports
            new_lon = (existing.longitude * existing.contributing_reports_count + avg_lon * len(report_ids)) / total_reports

            # Update in DB
            stmt = (
                update(CompositeHotspot)
                .where(CompositeHotspot.id == existing.id)
                .values(
                    latitude=new_lat,
                    longitude=new_lon,
                    aggregated_emotions=aggregated_emotions,
                    average_panic_level=avg_panic,
                    event_types=event_types,
                    severity_level=severity_level,
                    risk_level=risk_level,
                    contributing_reports_count=total_reports,
                )
            )
            await self.db.execute(stmt)
            await self.db.commit()

            # Refresh
            await self.db.refresh(existing)
            return {
                "latitude": existing.latitude,
                "longitude": existing.longitude,
                "aggregated_emotions": existing.aggregated_emotions,
                "average_panic_level": existing.average_panic_level,
                "event_types": existing.event_types,
                "severity_level": existing.severity_level,
                "risk_level": existing.risk_level,
                "contributing_reports": existing.contributing_reports_count,
            }

        else:
            # Create new
            COMPOSITE_HOTSPOTS_CREATED.inc()
            new_hotspot = CompositeHotspot(
                latitude=avg_lat,
                longitude=avg_lon,
                aggregated_emotions={k: v / len(cluster_points) for k, v in emotion_agg.items()},
                average_panic_level=sum(panic_scores) / len(cluster_points) if panic_scores else 0.0,
                event_types=list(event_types_set),
                severity_level=rev_severity.get(max(severity_vals) if severity_vals else 1, "low"),
                risk_level=risk_counts.most_common(1)[0][0] if risk_counts else "unknown",
                contributing_reports_count=len(report_ids),
            )

            self.db.add(new_hotspot)
            await self.db.commit()
            await self.db.refresh(new_hotspot)

            return {
                "latitude": new_hotspot.latitude,
                "longitude": new_hotspot.longitude,
                "aggregated_emotions": new_hotspot.aggregated_emotions,
                "average_panic_level": new_hotspot.average_panic_level,
                "event_types": new_hotspot.event_types,
                "severity_level": new_hotspot.severity_level,
                "risk_level": new_hotspot.risk_level,
                "contributing_reports": new_hotspot.contributing_reports_count,
            }

    async def generate_map_json_with_persistence(self) -> List[CompositeHotspotOutput]:
        start_time = time.time()
        logger.info("Starting map generation")

        # Import models here to avoid circular imports
        from core.models import HumanHotspot, DisasterHotspot, AggregateStatus, Report

        # Query pending hotspots
        human_stmt = select(HumanHotspot).where(HumanHotspot.status == AggregateStatus.pending)
        disaster_stmt = select(DisasterHotspot).where(DisasterHotspot.status == AggregateStatus.pending)

        human_result = await self.db.execute(human_stmt)
        disaster_result = await self.db.execute(disaster_stmt)
        humans = human_result.scalars().all()
        disasters = disaster_result.scalars().all()

        logger.info(f"Processing {len(humans)} human and {len(disasters)} disaster hotspots")

        # Assemble points
        points = await self.assemble_unified_points(humans, disasters)
        if not points:
            logger.info("No valid geocoded points found")
            return []

        # Cluster
        clusters = self.cluster_points(points)
        CLUSTERS_CREATED.inc(len(clusters))
        logger.info(f"Created {len(clusters)} clusters")

        # Process clusters
        output_list = []
        for cluster_points in clusters.values():
            try:
                hotspot_data = await self.update_or_create_composite_hotspot(cluster_points)
                output_list.append(CompositeHotspotOutput(**hotspot_data))
            except Exception as e:
                logger.error(f"Failed to process cluster: {e}")
                continue

        # Mark source hotspots as aggregated
        for p in points:
            payload = p["payload"]
            if p["type"] == "human":
                payload.status = AggregateStatus.aggregated
            elif p["type"] == "disaster":
                payload.status = AggregateStatus.aggregated

        await self.db.commit()
        PROCESSING_DURATION.observe(time.time() - start_time)
        logger.info(f"Map generation completed in {time.time() - start_time:.2f}s")

        return output_list
