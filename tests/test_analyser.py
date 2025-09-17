# tests/test_analyser.py
import pytest
from src.analyser.analyser import AnalyserA, Report, AnalysisOutput

@pytest.fixture
def analyser():
    return AnalyserA()

def test_analyze_emotions_empty(analyser):
    emotions = analyser.analyze_emotions("")
    assert len(emotions) == 1
    assert emotions[0].emotion == "neutral"
    assert emotions[0].score == 1.0

def test_analyze_emotions_sample(analyser):
    emotions = analyser.analyze_emotions("I am terrified and angry!")
    assert len(emotions) > 0
    emotion_names = [e.emotion for e in emotions]
    assert "fear" in emotion_names or "anger" in emotion_names

def test_estimate_panic_level(analyser):
    from src.analyser.analyser import EmotionScore
    emotions = [
        EmotionScore(emotion="fear", score=0.8),
        EmotionScore(emotion="anger", score=0.7)
    ]
    panic = analyser.estimate_panic_level(emotions)
    assert panic in ["high", "medium"]  # 0.8*0.9 + 0.7*0.8 = 1.28 → high

def test_analyze_reports(analyser):
    reports = [
        Report(
            event_type="riot",
            location="Paris",
            timestamp="2025-09-14T12:00:00Z",
            description="People are scared. Others are furious.",
            source="twitter",
            confidence=0.85
        )
    ]
    output = analyser.analyze_reports(reports)
    assert len(output.human_hotspots) >= 2  # at least 2 sentences
    assert len(output.disaster_hotspots) == 1
    assert output.disaster_hotspots[0].risk_level == "medium"

def test_sanitize_text(analyser):
    dirty = "Hello\x00World\x01Test"
    clean = analyser._sanitize_text(dirty)
    assert "\x00" not in clean
    assert "\x01" not in clean