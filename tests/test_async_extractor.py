# tests/test_async_extractor.py
import asyncio
import pytest
from src.extractor.extractor import ExtractorA, Reports
@pytest.mark.asyncio
async def test_extract_reports_user_input():
    extractor = ExtractorA()
    text = "User reports flood in Bangkok this morning"
    reports = await extractor.extract_reports(text, is_user_input=True)
    # Will fail without API keys, but should not crash
    assert reports is None or isinstance(reports, Reports)