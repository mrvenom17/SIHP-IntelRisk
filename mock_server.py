#!/usr/bin/env python3
"""
Mock server for disaster intelligence pipeline testing
Runs without requiring API keys or external dependencies
"""

import asyncio
import json
import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock data storage
mock_raw_posts = []
mock_reports = []
mock_human_hotspots = []
mock_disaster_hotspots = []
mock_composite_hotspots = []

# === 1. Pydantic Models ===

class RawPostInput(BaseModel):
    content: Dict[str, str]

class MapResponse(BaseModel):
    hotspots: List[Dict[str, Any]]

# === 2. Mock Extractor ===

class MockExtractor:
    def __init__(self):
        self.extraction_count = 0

    async def extract_reports(self, text: str, is_user_input: bool = False):
        self.extraction_count += 1
        logger.info(f"Mock extractor processing: {text[:50]}...")

        # Generate mock reports based on text content
        reports = []

        if "flood" in text.lower():
            report = {
                "event_type": "flood",
                "location": "Chennai" if "chennai" in text.lower() else "Unknown",
                "timestamp": "2024-01-15T10:30:00Z",
                "description": text,
                "source": "mock_social_media",
                "confidence": 0.8,
                "veracity_flag": "unconfirmed"
            }
            reports.append(report)

        if "tsunami" in text.lower():
            report = {
                "event_type": "tsunami",
                "location": "Andaman Coast" if "andaman" in text.lower() else "Unknown",
                "timestamp": "2024-01-15T11:00:00Z",
                "description": text,
                "source": "mock_news_agency",
                "confidence": 0.9,
                "veracity_flag": "confirmed"
            }
            reports.append(report)

        # Always return at least one report for testing
        if not reports:
            report = {
                "event_type": "disaster",
                "location": "Unknown",
                "timestamp": "2024-01-15T12:00:00Z",
                "description": text,
                "source": "mock_user_input",
                "confidence": 0.7,
                "veracity_flag": "unknown"
            }
            reports.append(report)

        return {"reports": reports}

# === 3. Mock Checker ===

class MockChecker:
    def __init__(self):
        self.check_count = 0

    async def run_async(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.check_count += len(reports)
        logger.info(f"Mock checker processing {len(reports)} reports")

        verified = []
        for report in reports:
            # Accept most reports for testing
            if report.get("confidence", 0) > 0.5:
                report["veracity_flag"] = "verified"
                verified.append(report)
            else:
                report["veracity_flag"] = "rejected"

        logger.info(f"Mock checker verified {len(verified)}/{len(reports)} reports")
        return verified

# === 4. Mock Analyser ===

class MockAnalyser:
    def __init__(self):
        self.analysis_count = 0

    async def analyze_reports_async(self, reports: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        self.analysis_count += len(reports)
        logger.info(f"Mock analyser processing {len(reports)} reports")

        human_hotspots = []
        disaster_hotspots = []

        for report in reports:
            # Create human hotspot
            human_hotspot = {
                "location": report.get("location", "Unknown"),
                "timestamp": report.get("timestamp", "2024-01-15T12:00:00Z"),
                "emotions": [{"emotion": "fear", "score": 0.8}, {"emotion": "panic", "score": 0.6}],
                "panic_level": "high",
                "affected_population_estimate": 1000
            }
            human_hotspots.append(human_hotspot)

            # Create disaster hotspot
            disaster_hotspot = {
                "location": report.get("location", "Unknown"),
                "timestamp": report.get("timestamp", "2024-01-15T12:00:00Z"),
                "event_type": report.get("event_type", "unknown"),
                "severity": "high",
                "risk_level": "high",
                "description_summary": report.get("description", "")[:200]
            }
            disaster_hotspots.append(disaster_hotspot)

        return {
            "human_hotspots": human_hotspots,
            "disaster_hotspots": disaster_hotspots
        }

# === 5. Mock Detecter ===

class MockDetecter:
    def __init__(self):
        self.detection_count = 0

    async def generate_map_json_with_persistence(self) -> List[Dict[str, Any]]:
        self.detection_count += 1
        logger.info("Mock detecter generating composite hotspots")

        # Create mock composite hotspots
        hotspots = [
            {
                "latitude": 13.0827,
                "longitude": 80.2707,
                "aggregated_emotions": {"fear": 0.8, "panic": 0.6},
                "average_panic_level": 0.7,
                "event_types": ["flood"],
                "severity_level": "high",
                "risk_level": "high",
                "contributing_reports": 3
            },
            {
                "latitude": 11.6234,
                "longitude": 92.7265,
                "aggregated_emotions": {"fear": 0.9, "panic": 0.8},
                "average_panic_level": 0.85,
                "event_types": ["tsunami"],
                "severity_level": "critical",
                "risk_level": "critical",
                "contributing_reports": 2
            }
        ]

        return hotspots

# === 6. FastAPI App ===

app = FastAPI(title="Mock Disaster Intelligence Server")

# Initialize mock agents
mock_extractor = MockExtractor()
mock_checker = MockChecker()
mock_analyser = MockAnalyser()
mock_detecter = MockDetecter()

@app.post("/api/ingest")
async def ingest_data(post_input: RawPostInput):
    """Ingest raw text data and process through the full pipeline"""
    logger.info(f"Ingesting data: {post_input.content}")

    # Store raw post
    post_id = len(mock_raw_posts) + 1
    raw_post = {
        "id": post_id,
        "content": post_input.content,
        "timestamp": "2024-01-15T12:00:00Z",
        "status": "pending"
    }
    mock_raw_posts.append(raw_post)

    # Step 1: Extract
    text = post_input.content.get("text", "")
    extracted = await mock_extractor.extract_reports(text)
    reports = extracted.get("reports", [])

    logger.info(f"Extracted {len(reports)} reports")

    # Step 2: Check
    verified_reports = await mock_checker.run_async(reports)
    logger.info(f"Verified {len(verified_reports)} reports")

    # Step 3: Analyze
    analysis = await mock_analyser.analyze_reports_async(verified_reports)
    human_hotspots = analysis.get("human_hotspots", [])
    disaster_hotspots = analysis.get("disaster_hotspots", [])

    logger.info(f"Generated {len(human_hotspots)} human hotspots and {len(disaster_hotspots)} disaster hotspots")

    # Step 4: Detect (generate composite hotspots)
    composite_hotspots = await mock_detecter.generate_map_json_with_persistence()
    logger.info(f"Generated {len(composite_hotspots)} composite hotspots")

    return {
        "message": "Data processed successfully",
        "pipeline_results": {
            "raw_posts": 1,
            "extracted_reports": len(reports),
            "verified_reports": len(verified_reports),
            "human_hotspots": len(human_hotspots),
            "disaster_hotspots": len(disaster_hotspots),
            "composite_hotspots": len(composite_hotspots)
        }
    }

@app.get("/api/map/latest")
async def get_latest_map():
    """Get the latest disaster map data"""
    composite_hotspots = await mock_detecter.generate_map_json_with_persistence()

    if not composite_hotspots:
        raise HTTPException(status_code=404, detail="No map data available")

    return {"hotspots": composite_hotspots}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "mock_server": True}

@app.get("/metrics")
async def get_metrics():
    """Get processing metrics"""
    return {
        "extractor_calls": mock_extractor.extraction_count,
        "checker_calls": mock_checker.check_count,
        "analyser_calls": mock_analyser.analysis_count,
        "detecter_calls": mock_detecter.detection_count,
        "total_raw_posts": len(mock_raw_posts),
        "total_reports": len(mock_reports),
        "total_human_hotspots": len(mock_human_hotspots),
        "total_disaster_hotspots": len(mock_disaster_hotspots),
        "total_composite_hotspots": len(mock_composite_hotspots)
    }

# === 7. Main ===

if __name__ == "__main__":
    print("🚀 Starting Mock Disaster Intelligence Server...")
    print("📡 Server will be available at http://localhost:8000")
    print("📋 Available endpoints:")
    print("   POST /api/ingest - Process disaster reports")
    print("   GET  /api/map/latest - Get latest disaster map")
    print("   GET  /health - Health check")
    print("   GET  /metrics - Processing metrics")
    print("\n🔧 No API keys required - all agents are mocked!")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
