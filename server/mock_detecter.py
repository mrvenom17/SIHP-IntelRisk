#!/usr/bin/env python3
"""
Mock Detecter for testing without database dependencies
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MockDetecterA:
    """Mock detecter that generates realistic hotspots without database"""

    def __init__(self, db_session=None):
        self.db = db_session

    async def generate_map_json_with_persistence(self) -> List[Dict[str, Any]]:
        """Generate mock composite hotspots"""

        logger.info("🗺️ Using Mock Detecter (no database required)")

        # Generate mock hotspots based on typical disaster scenarios
        mock_hotspots = [
            {
                "latitude": 13.0827,
                "longitude": 80.2707,
                "aggregated_emotions": {"fear": 0.8, "anxiety": 0.6, "concern": 0.4},
                "average_panic_level": 0.7,
                "event_types": ["flood", "storm_surge"],
                "severity_level": "high",
                "risk_level": "critical",
                "contributing_reports": 5
            },
            {
                "latitude": 11.6234,
                "longitude": 92.7265,
                "aggregated_emotions": {"fear": 0.9, "panic": 0.8, "urgency": 0.7},
                "average_panic_level": 0.85,
                "event_types": ["tsunami", "high_waves"],
                "severity_level": "critical",
                "risk_level": "extreme",
                "contributing_reports": 3
            },
            {
                "latitude": 19.0760,
                "longitude": 72.8777,
                "aggregated_emotions": {"concern": 0.5, "anxiety": 0.4, "fear": 0.3},
                "average_panic_level": 0.4,
                "event_types": ["coastal_erosion", "high_waves"],
                "severity_level": "medium",
                "risk_level": "moderate",
                "contributing_reports": 2
            }
        ]

        logger.info(f"✅ Mock Detecter generated {len(mock_hotspots)} composite hotspots")
        return mock_hotspots
