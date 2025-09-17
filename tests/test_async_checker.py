# tests/test_async_checker.py
import asyncio
import pytest
from src.checker.checker import CheckerA, Report

@pytest.mark.asyncio
async def test_run_async():
    checker = CheckerA()
    reports = [
        Report(
            event_type="earthquake",
            location="Tokyo",
            timestamp="2025-09-14T12:00:00Z",
            description="Strong shaking felt in city center",
            source="official_news_agency",
            confidence=0.92
        )
    ]
    result = await checker.run_async(reports)
    assert len(result) == 1
    assert result[0].event_type == "earthquake"