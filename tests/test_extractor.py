# tests/test_extractor.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.extractor.extractor import ExtractorA, Reports, Report
from datetime import datetime, timezone

@pytest.fixture
def extractor():
    return ExtractorA()

@pytest.mark.asyncio
async def test_sanitize_input(extractor):
    dirty = "Hello\x00World{malicious}!"
    clean = extractor.sanitize_input(dirty)
    assert "\x00" not in clean
    assert "{{" in clean  # ✅ CHANGED: expect escaped braces, not removed
    assert "}}" in clean

def test_normalize_relative_times(extractor):
    text = "Flood happened last night in Jakarta"
    normalized = extractor.normalize_relative_times(text, datetime(2025, 9, 15))
    assert "2025-09-14T20:00:00Z" in normalized

# ✅ FIXED: Patch 'requests.Session' — not the full module path
@pytest.fixture
def mock_session_class():
    with patch('requests.Session') as mock:
        yield mock

@pytest.mark.asyncio
async def test_extract_from_perplexity_success(mock_session_class, extractor):
    # Create extractor instance
    extractor = ExtractorA()
    
    # Mock the session's post method directly
    with patch.object(extractor.session, 'post') as mock_post:
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"reports": [{"event_type": "flood", "location": "Jakarta", "description": "Water rising", "source": "news", "confidence": 0.9, "veracity_flag": "confirmed"}]}'
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        reports = await extractor.extract_from_perplexity("Flood in Jakarta")
        assert len(reports.reports) == 1
        assert reports.reports[0].event_type == "flood"
        assert reports.reports[0].location == "Jakarta"
        assert reports.reports[0].confidence == 0.9

@pytest.mark.asyncio
@patch('src.extractor.extractor.ThreadSafeGemini.get_instance')
async def test_extract_from_gemini_success(mock_gemini, extractor):
    mock_llm = MagicMock()
    # ✅ Return pure JSON — no Markdown
    mock_llm.invoke.return_value.content = '{"reports": [{"event_type": "fire", "location": "LA", "description": "Wildfire", "source": "user", "confidence": 0.8, "veracity_flag": "confirmed"}]}'
    mock_gemini.return_value = mock_llm

    reports = await extractor.extract_from_gemini("Fire in LA")
    assert len(reports.reports) == 1
    assert reports.reports[0].event_type == "fire"

@pytest.mark.asyncio
async def test_post_process_reports(extractor):
    # ✅ FIXED: Convert datetime to ISO string
    report = Report(
        event_type="wildfire",
        location="unknown",
        timestamp=datetime.now(timezone.utc).isoformat(),  # ← FIXED
        source="official",
        reporter="authority",
        description="Officials confirmed no wildfire here",
        confidence=0.9,
        veracity_flag="unverified"
    )
    reports = Reports(reports=[report])
    processed = extractor.post_process_reports(reports)
    
    assert len(processed.reports) == 1
    assert processed.reports[0].veracity_flag == "retracted"
    assert processed.reports[0].confidence <= 0.5