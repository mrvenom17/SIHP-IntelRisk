#!/usr/bin/env python3
"""
SIEM Server - Main API Server with Mock Extractor
Receives requests and forwards them to the complete pipeline using mock data
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import mock extractor instead of real one
from server.mock_extractor import MockExtractorA
from src.detecter.detecter import DetecterA
from src.checker.checker import CheckerA

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="SIEM Server (Mock Mode)",
    description="Central Security Hub for Monitoring & Compliance - Using Mock Data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class DisasterReportRequest(BaseModel):
    text: str = Field(..., description="Text input for disaster analysis")
    source: Optional[str] = Field("user_input", description="Source of the input")

class DisasterReportResponse(BaseModel):
    success: bool
    reports: List[Dict[str, Any]] = Field(default_factory=list)
    hotspots: List[Dict[str, Any]] = Field(default_factory=list)
    verified_reports: List[Dict[str, Any]] = Field(default_factory=list)
    message: str = Field(..., description="Response message")
    error: Optional[str] = Field(None, description="Error message if any")

# Global instances
extractor = None
detecter = None
checker = None

async def initialize_components():
    """Initialize all pipeline components"""
    global extractor, detecter, checker

    try:
        logger.info("🔧 Initializing Mock Extractor...")
        extractor = MockExtractorA()  # Use mock extractor

        logger.info("🔧 Initializing Detecter...")
        detecter = DetecterA(db_session=None)  # Will use mock for now

        logger.info("🔧 Initializing Checker...")
        checker = CheckerA()

        logger.info("✅ All components initialized successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("🚀 Starting SIEM Server (Mock Mode)...")
    success = await initialize_components()
    if not success:
        logger.error("❌ Failed to initialize server components")
        raise RuntimeError("Server initialization failed")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "SIEM Server (Mock Mode) is running",
        "version": "1.0.0",
        "mode": "mock"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "extractor": extractor is not None,
            "detecter": detecter is not None,
            "checker": checker is not None
        },
        "message": "All systems operational (Mock Mode)",
        "mode": "mock"
    }

@app.post("/analyze", response_model=DisasterReportResponse)
async def analyze_disaster(request: DisasterReportRequest):
    """
    Analyze disaster text and generate complete pipeline output
    """
    try:
        logger.info(f"📥 Received analysis request: {request.text[:100]}...")

        if not all([extractor, detecter, checker]):
            raise HTTPException(
                status_code=503,
                detail="Server components not initialized"
            )

        # Step 1: Extract reports using the mock extractor
        logger.info("🔍 Step 1: Extracting reports...")
        if not extractor:
            raise HTTPException(status_code=503, detail="Extractor not initialized")

        try:
            reports = await extractor.extract_reports(request.text, is_user_input=True)
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            error_msg = str(e).strip("'\"")  # Clean up quotes from error message
            raise HTTPException(status_code=500, detail=f"Extraction failed: {error_msg}")

        if not reports or not reports.reports:
            return DisasterReportResponse(
                success=False,
                reports=[],
                hotspots=[],
                verified_reports=[],
                message="No disaster reports extracted from the input text",
                error="No reports found"
            )

        logger.info(f"✅ Extracted {len(reports.reports)} reports")

        # Step 2: Detect hotspots using mock detecter
        logger.info("🔍 Step 2: Detecting hotspots...")
        try:
            if not detecter:
                raise HTTPException(status_code=503, detail="Detecter not initialized")

            hotspots = await detecter.generate_map_json_with_persistence()
            logger.info(f"✅ Generated {len(hotspots)} composite hotspots")
        except Exception as e:
            logger.warning(f"⚠️ Hotspot detection failed: {e}")
            hotspots = []

        # Step 3: Verify reports (mock for now)
        logger.info("🔍 Step 3: Verifying reports...")
        try:
            # For now, mark all reports as verified
            verified_reports = []
            for report in reports.reports:
                verified_reports.append({
                    "original_report": {
                        "event_type": report.event_type,
                        "location": report.location,
                        "description": report.description
                    },
                    "verification_status": "verified",
                    "confidence_score": report.confidence or 0.8,
                    "verification_details": {
                        "source_trusted": True,
                        "cluster_size": 1
                    }
                })
            logger.info(f"✅ Verified {len(verified_reports)} reports")
        except Exception as e:
            logger.warning(f"⚠️ Report verification failed: {e}")
            verified_reports = []

        # Convert reports to dict for JSON response
        reports_dict = []
        for report in reports.reports:
            reports_dict.append({
                "event_type": report.event_type,
                "location": report.location,
                "timestamp": report.timestamp,
                "description": report.description,
                "source": report.source,
                "confidence": report.confidence,
                "veracity_flag": report.veracity_flag,
                "media_urls": report.media_urls or [],
                "reporter": report.reporter
            })

        # Convert hotspots to dict
        hotspots_dict = []
        for hotspot in hotspots:
            hotspots_dict.append({
                "location": hotspot.get("location", "Unknown"),
                "coordinates": hotspot.get("coordinates", []),
                "severity": hotspot.get("severity", "medium"),
                "event_count": hotspot.get("event_count", 0),
                "risk_level": hotspot.get("risk_level", "medium")
            })

        # Convert verified reports to dict
        verified_dict = []
        for verified in verified_reports:
            verified_dict.append({
                "original_report": verified.get("original_report", {}),
                "verification_status": verified.get("verification_status", "unknown"),
                "confidence_score": verified.get("confidence_score", 0.0),
                "verification_details": verified.get("verification_details", {})
            })

        return DisasterReportResponse(
            success=True,
            reports=reports_dict,
            hotspots=hotspots_dict,
            verified_reports=verified_dict,
            message=f"Successfully processed {len(reports.reports)} disaster reports",
            error=None
        )

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/extract")
async def extract_only(request: DisasterReportRequest):
    """Extract reports only (for testing)"""
    try:
        if not extractor:
            raise HTTPException(status_code=503, detail="Extractor not initialized")

        reports = await extractor.extract_reports(request.text, is_user_input=True)

        if not reports or not reports.reports:
            return {
                "success": False,
                "reports": [],
                "message": "No reports extracted"
            }

        reports_dict = []
        for report in reports.reports:
            reports_dict.append({
                "event_type": report.event_type,
                "location": report.location,
                "timestamp": report.timestamp,
                "description": report.description,
                "source": report.source,
                "confidence": report.confidence,
                "veracity_flag": report.veracity_flag
            })

        return {
            "success": True,
            "reports": reports_dict,
            "message": f"Extracted {len(reports.reports)} reports"
        }

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        error_msg = str(e).strip("'\"")  # Clean up quotes from error message
        raise HTTPException(status_code=500, detail=f"Extraction failed: {error_msg}")

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    return {
        "status": "running",
        "components_initialized": {
            "extractor": extractor is not None,
            "detecter": detecter is not None,
            "checker": checker is not None
        },
        "uptime": "Server is running",
        "version": "1.0.0",
        "mode": "mock"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
