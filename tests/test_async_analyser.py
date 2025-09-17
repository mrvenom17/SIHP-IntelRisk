# tests/test_async_analyser.py
import asyncio
import pytest
from src.analyser.analyser import AnalyserA, Report

@pytest.mark.asyncio
async def test_analyze_reports_async():
    analyser = AnalyserA()
    reports = [
        Report(
            event_type="flood",
            location="Bangkok",
            description="Water is rising fast. People are panicking.",
            timestamp="2025-09-14T13:00:00Z"
        )
    ]
    output = await analyser.analyze_reports_async(reports)
    assert len(output.human_hotspots) > 0
    assert output.disaster_hotspots[0].severity == "high"