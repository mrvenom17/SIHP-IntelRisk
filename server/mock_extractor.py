#!/usr/bin/env python3
"""
Mock Extractor for testing without API keys
"""

import json
import logging
from typing import Optional, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Report(BaseModel):
    event_type: Optional[str] = Field(None, description="Type of disaster/event")
    location: Optional[str] = Field(None, description="Location of the event")
    timestamp: Optional[str] = Field(None, description="ISO8601 datetime")
    description: Optional[str] = Field(None, description="Full textual description")
    source: Optional[str] = Field(None, description="Information source")
    media_urls: Optional[List[str]] = Field(default_factory=list)
    reporter: Optional[str] = Field(None, description="Name or ID of original poster")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    veracity_flag: Optional[str] = Field(None, description="confirmed, unconfirmed, retracted, unknown")

class Reports(BaseModel):
    reports: List[Report]

class MockExtractorA:
    """Mock extractor that generates realistic disaster reports without API calls"""

    def __init__(self, config=None):
        self.config = config or {}

    def _infer_event_type(self, text: str) -> str:
        text_lower = text.lower()
        if "flood" in text_lower:
            return "flood"
        elif "tsunami" in text_lower:
            return "tsunami"
        elif "storm" in text_lower or "surge" in text_lower:
            return "storm_surge"
        elif "wave" in text_lower:
            return "high_waves"
        elif "erosion" in text_lower:
            return "coastal_erosion"
        elif "current" in text_lower:
            return "abnormal_currents"
        elif "panic" in text_lower:
            return "crowd_panic"
        else:
            return "other"

    def _infer_location(self, text: str) -> str:
        locations = [
            "chennai", "andaman", "puri", "kerala", "mumbai",
            "odisha", "goa", "tamil nadu", "lakshadweep",
            "visakhapatnam", "kolkata", "kanyakumari", "pondicherry"
        ]
        text_lower = text.lower()
        for loc in locations:
            if loc in text_lower:
                return loc.title()
        return "Unknown"

    async def extract_reports(self, input_text: str, is_user_input: bool = False) -> Optional[Reports]:
        """Generate mock disaster reports based on input text"""

        logger.info("🔍 Using Mock Extractor (no API keys required)")

        # Create a realistic report based on the input
        event_type = self._infer_event_type(input_text)
        location = self._infer_location(input_text)

        # Create a more detailed description
        description = input_text
        if len(description) > 200:
            description = description[:200] + "..."

        report = Report(
            event_type=event_type,
            location=location,
            timestamp="2025-01-21T10:00:00Z",
            description=description,
            source="mock_data",
            confidence=0.9,
            veracity_flag="confirmed"
        )

        reports = Reports(reports=[report])

        logger.info(f"✅ Mock Extractor generated {len(reports.reports)} reports")
        return reports
