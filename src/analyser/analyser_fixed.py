# src/analyser/analyser_fixed.py
import asyncio
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from transformers import pipeline
from nltk.tokenize import sent_tokenize
import nltk
import time
from prometheus_client import Counter as PrometheusCounter, Histogram

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
ANALYSIS_DURATION = Histogram('analyser_analysis_duration_seconds', 'Time spent analyzing reports')
EMOTION_CLASSIFICATIONS = PrometheusCounter('analyser_emotion_classifications_total', 'Total emotion classifications performed')
PANIC_SCORES = Histogram('analyser_panic_scores', 'Distribution of computed panic scores')

# Download NLTK data at startup
try:
    nltk.data.find('tokenizers/punkt')
    logger.info("NLTK punkt tokenizer found")
except LookupError:
    try:
        nltk.data.find('tokenizers/punkt_tab')
        logger.info("NLTK punkt_tab tokenizer found")
    except LookupError:
        logger.info("Downloading NLTK punkt tokenizer...")
        try:
            nltk.download('punkt_tab', quiet=True)
            logger.info("NLTK punkt_tab downloaded successfully")
        except Exception as e:
            logger.warning(f"Failed to download punkt_tab: {e}, trying punkt...")
            try:
                nltk.download('punkt', quiet=True)
                logger.info("NLTK punkt downloaded successfully")
            except Exception as e2:
                logger.error(f"Failed to download NLTK data: {e2}")

# === 1. Report and Analysis schema ===

class Report(BaseModel):
    event_type: Optional[str] = None
    location: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

class EmotionScore(BaseModel):
    emotion: str
    score: float = Field(..., ge=0.0, le=1.0)

class HumanHotspot(BaseModel):
    location: Optional[str] = None
    timestamp: Optional[str] = None
    emotions: List[EmotionScore]
    panic_level: str
    affected_population_estimate: Optional[int] = None

class DisasterHotspot(BaseModel):
    location: Optional[str] = None
    timestamp: Optional[str] = None
    event_type: Optional[str] = None
    severity: str
    risk_level: str
    description_summary: Optional[str] = None

class AnalysisOutput(BaseModel):
    human_hotspots: List[HumanHotspot]
    disaster_hotspots: List[DisasterHotspot]

# === 2. AnalyserA ===

class AnalyserA:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.severity_map = config.get("severity_map", {
            "fire": "high",
            "flood": "high",
            "earthquake": "very_high",
            "riot": "medium",
            "storm": "medium",
            "inundation": "high",
            "": "low",
            None: "low"
        })
        self.panic_weights = config.get("panic_weights", {
            "panic": 1.0,
            "fear": 0.9,
            "anger": 0.8,
            "sadness": 0.6,
            "disgust": 0.5,
            "neutral": 0.0,
            "joy": 0.0,
            "surprise": 0.3,
        })
        self.max_description_length = config.get("max_description_length", 2000)
        self.model_name = config.get("model_name", "j-hartmann/emotion-english-distilroberta-base")
        self._emotion_classifier = None

    @property
    def emotion_classifier(self):
        if self._emotion_classifier is None:
            logger.info(f"Loading emotion classifier model: {self.model_name}")
            try:
                # Use a simpler, more reliable model
                self._emotion_classifier = pipeline(
                    "text-classification",
                    model="cardiffnlp/twitter-roberta-base-emotion-multilabel-latest",
                    top_k=None,
                    truncation=True,
                    max_length=512,
                    device=-1  # Use CPU to avoid GPU issues
                )
                logger.info("✅ Emotion classifier loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load model: {e}")
                logger.info("🔄 Falling back to mock emotion classifier")
                self._emotion_classifier = self._mock_emotion_classifier
        return self._emotion_classifier

    def _mock_emotion_classifier(self, text: str):
        """Mock emotion classifier for testing when real model fails"""
        logger.info(f"Mock classifier analyzing: {text[:50]}...")
        # Return some basic emotions based on keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ["panic", "fear", "scared", "terrified"]):
            return [{"label": "fear", "score": 0.8}]
        elif any(word in text_lower for word in ["angry", "furious", "outraged"]):
            return [{"label": "anger", "score": 0.7}]
        elif any(word in text_lower for word in ["sad", "devastated", "loss"]):
            return [{"label": "sadness", "score": 0.6}]
        else:
            return [{"label": "neutral", "score": 0.5}]

    def _sanitize_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        # Remove control characters except newlines/tabs
        sanitized = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')
        return sanitized[:self.max_description_length]

    def analyze_emotions(self, text: str) -> List[EmotionScore]:
        text = self._sanitize_text(text)
        if not text.strip():
            return [EmotionScore(emotion="neutral", score=1.0)]

        try:
            start_time = time.time()
            results = self.emotion_classifier(text)
            EMOTION_CLASSIFICATIONS.inc()
            ANALYSIS_DURATION.observe(time.time() - start_time)

            # Handle different return formats
            if isinstance(results, list) and len(results) > 0:
                if isinstance(results[0], dict):
                    # Format: [{"label": "emotion", "score": 0.8}]
                    all_scores = results
                elif isinstance(results[0], list):
                    # Format: [[{"label": "emotion", "score": 0.8}]]
                    all_scores = results[0]
                else:
                    all_scores = []
            else:
                all_scores = []

            emotions = [
                EmotionScore(emotion=e['label'].lower(), score=e['score'])
                for e in all_scores
            ]
            return emotions
        except Exception as e:
            logger.error(f"Emotion classification failed for text: '{text[:50]}...': {e}")
            return [EmotionScore(emotion="error", score=0.0)]

    def estimate_panic_level(self, emotions: List[EmotionScore]) -> str:
        panic_score = sum(em.score * self.panic_weights.get(em.emotion, 0.0) for em in emotions)
        PANIC_SCORES.observe(panic_score)
        if panic_score >= 1.0:
            return "high"
        elif panic_score >= 0.5:
            return "medium"
        else:
            return "low"

    def estimate_risk_level(self, severity: str) -> str:
        if severity == "very_high":
            return "critical"
        elif severity == "high":
            return "high"
        elif severity == "medium":
            return "medium"
        else:
            return "low"

    def analyze_human_response_chunks(self, report: Report) -> List[HumanHotspot]:
        """
        Split description into chunks (sentences) and analyze each for emotions.
        Returns list of HumanHotspot objects.
        """
        description = self._sanitize_text(report.description or "")
        chunks = []

        if description:
            try:
                # Primary: NLTK sentence tokenizer
                chunks = sent_tokenize(description)
            except Exception as e:
                logger.warning(f"NLTK tokenization failed: {e}. Falling back to manual splitting.")
                # Fallback: Split by periods, exclamation, question marks
                import re
                chunks = re.split(r'[.!?]+', description)
                # Filter out empty/whitespace-only chunks
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        if not chunks:
            chunks = [""]  # Ensure at least one chunk for testing

        human_hotspots = []
        for chunk in chunks:
            emotions = self.analyze_emotions(chunk)
            panic_level = self.estimate_panic_level(emotions)
            hotspot = HumanHotspot(
                location=report.location,
                timestamp=report.timestamp,
                emotions=emotions,
                panic_level=panic_level,
                affected_population_estimate=None
            )
            human_hotspots.append(hotspot)

        return human_hotspots

    def analyze_disaster_hotspot(self, report: Report) -> DisasterHotspot:
        event_type = (report.event_type or "").lower() if report.event_type else ""
        severity = self.severity_map.get(event_type, "low")
        risk_level = self.estimate_risk_level(severity)
        description_summary = (report.description[:200] if report.description else None)

        return DisasterHotspot(
            location=report.location,
            timestamp=report.timestamp,
            event_type=report.event_type,
            severity=severity,
            risk_level=risk_level,
            description_summary=description_summary
        )

    def analyze_reports(self, reports: List[Report]) -> AnalysisOutput:
        all_human_hotspots = []
        all_disaster_hotspots = []

        for report in reports:
            try:
                human_hotspots = self.analyze_human_response_chunks(report)
                disaster_hotspot = self.analyze_disaster_hotspot(report)
                all_human_hotspots.extend(human_hotspots)
                all_disaster_hotspots.append(disaster_hotspot)
            except Exception as e:
                logger.error(f"Failed to analyze report {report}: {e}")
                continue  # Skip bad reports, don't crash entire batch

        return AnalysisOutput(
            human_hotspots=all_human_hotspots,
            disaster_hotspots=all_disaster_hotspots
        )

    async def analyze_reports_async(self, reports: List[Report]) -> AnalysisOutput:
        """Async wrapper for non-blocking I/O in web servers"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze_reports, reports)
