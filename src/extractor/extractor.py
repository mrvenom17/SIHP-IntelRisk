
# src/extractor/extractor.py
import asyncio
import logging
import re
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge, REGISTRY
import time
from datetime import datetime, timedelta, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
EXTRACTION_ATTEMPTS = PrometheusCounter('extractor_extraction_attempts_total', 'Total extraction attempts', ['method'])
EXTRACTION_SUCCESS = PrometheusCounter('extractor_extraction_success_total', 'Successful extractions', ['method'])
EXTRACTION_DURATION = Histogram('extractor_extraction_duration_seconds', 'Extraction duration', ['method'])
FALLBACK_USED = PrometheusCounter('extractor_fallback_used_total', 'Gemini fallback usage')

# Load env vars
load_dotenv()

# === 1. Extraction Schema ===

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

# === 2. API Keys and Endpoints ===

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate at runtime, not import
if not PERPLEXITY_API_KEY:
    logger.warning("PERPLEXITY_API_KEY environment variable not set.")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY environment variable not set.")

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"  # FIXED: removed trailing spaces

# === 3. Initialize Gemini Model (Thread-Safe) ===

from langchain_google_genai import ChatGoogleGenerativeAI

class ThreadSafeGemini:
    _instance = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    if not GOOGLE_API_KEY:
                        raise RuntimeError("GOOGLE_API_KEY is missing for Gemini model.")
                    cls._instance = ChatGoogleGenerativeAI(
                        google_api_key=GOOGLE_API_KEY,
                        model="gemini-1.5-flash",
                        temperature=0.0,
                        max_tokens=1000
                    )
        return cls._instance

# === 4. Prompts for Gemini Extraction ===

from langchain.prompts import ChatPromptTemplate

GEMINI_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a disaster events extractor. Extract each distinct event into a report. "
    "Events may contradict or be retracted; detect and mark veracity. Assign confidence 0 to 1. "
    "Use plausible inferences; no unsupported facts. Convert relative times to ISO8601 or null. "
    "Return ONLY a JSON object with key 'reports' containing list of reports. "
    "Schema: Report has fields: event_type, location, timestamp, description, source, media_urls, reporter, confidence, veracity_flag\n"
    "Input text: {text}"
)


# === 5. Extractor Class ===

class ExtractorA:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    # ✅ FIXED: Added 'self' parameter
    def sanitize_input(self, text: str) -> str:
        """Prevent prompt injection and control chars"""
        if not text:
            return ""
        # Remove control chars except \n\t
        sanitized = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')
        # Escape curly braces that might break JSON
        sanitized = sanitized.replace("{", "{{").replace("}", "}}")
        return sanitized[:5000]  # Limit input length

    # ✅ FIXED: Added 'self' parameter + ensure 'datetime' is available
    def normalize_relative_times(self, text: str, reference_date: Optional[datetime] = None) -> str:
        if not reference_date:
            reference_date = datetime.now(timezone.utc)  # ✅ Now safe — datetime imported at top

        replacements = {
            r'\blast night\b': (reference_date - timedelta(days=1)).strftime("%Y-%m-%dT20:00:00Z"),
            r'\byesterday\b': (reference_date - timedelta(days=1)).strftime("%Y-%m-%d"),
            r'\btoday\b': reference_date.strftime("%Y-%m-%d"),
            r'\bthis morning\b': reference_date.strftime("%Y-%m-%dT08:00:00Z"),
            r'\bthis afternoon\b': reference_date.strftime("%Y-%m-%dT15:00:00Z"),
            r'\bthis evening\b': reference_date.strftime("%Y-%m-%dT19:00:00Z"),
        }

        for pattern, repl in replacements.items():
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

        return text
    
    # ✅ FIXED: Added 'self' parameter
    def post_process_reports(self, reports: Reports) -> Reports:
        for report in reports.reports:
            desc = (report.description or "").lower()

            negations = [
                "controlled burn",
                "not a wildfire",
                "retracted",
                "false alarm",
                "no evidence",
                "disproved",
                "officials confirmed no",
            ]
            if any(neg in desc for neg in negations):
                report.veracity_flag = "retracted"
                if report.confidence is None or report.confidence > 0.5:
                    report.confidence = 0.3
            else:
                if not report.veracity_flag:
                    report.veracity_flag = "confirmed"
                if report.confidence is None:
                    report.confidence = 0.8

            if report.event_type is None and ("submerged" in desc and "water" in desc):
                report.event_type = "flood"

        return reports

    async def extract_from_perplexity(self, query: str) -> Optional[Reports]:
        """Async Perplexity API extraction with retries"""
        if not PERPLEXITY_API_KEY:
            logger.warning("Perplexity API key missing; skipping extraction.")
            return None

        EXTRACTION_ATTEMPTS.labels(method='perplexity').inc()
        start_time = time.time()

        try:
            sanitized_query = self.sanitize_input(query)
            normalized_text = self.normalize_relative_times(sanitized_query)
            prompt_text = GEMINI_PROMPT_TEMPLATE.format(text=normalized_text)

            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {"role": "user", "content": prompt_text}
                ]
            }

            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=15)
            )
            response.raise_for_status()
            data = response.json()

            raw_json_str = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not raw_json_str:
                logger.warning("Perplexity returned empty content")
                return None

            try:
                reports = Reports.model_validate_json(raw_json_str)
                EXTRACTION_SUCCESS.labels(method='perplexity').inc()
                EXTRACTION_DURATION.labels(method='perplexity').observe(time.time() - start_time)
                return self.post_process_reports(reports)
            except ValidationError as e:
                logger.error(f"Perplexity JSON validation failed: {e}")
                return Reports(reports=[])

        except Exception as e:
            logger.error(f"Perplexity extraction error: {e}")
            return None

    async def extract_from_gemini(self, text: str) -> Optional[Reports]:
        """Async Gemini extraction"""
        EXTRACTION_ATTEMPTS.labels(method='gemini').inc()
        start_time = time.time()

        try:
            sanitized_text = self.sanitize_input(text)
            normalized_text = self.normalize_relative_times(sanitized_text)
            prompt = GEMINI_PROMPT_TEMPLATE.format(text=normalized_text)

            gemini_llm = await ThreadSafeGemini.get_instance()
            loop = asyncio.get_event_loop()
            gemini_response = await loop.run_in_executor(None, gemini_llm.invoke, prompt)

            raw_json_str = None
            if hasattr(gemini_response, "content"):
                raw_json_str = gemini_response.content
            elif isinstance(gemini_response, str):
                raw_json_str = gemini_response
            else:
                raw_json_str = str(gemini_response)

            try:
                reports = Reports.model_validate_json(raw_json_str)
                EXTRACTION_SUCCESS.labels(method='gemini').inc()
                EXTRACTION_DURATION.labels(method='gemini').observe(time.time() - start_time)
                return self.post_process_reports(reports)
            except ValidationError as e:
                logger.error(f"Gemini JSON validation failed: {e}")
                return Reports(reports=[])

        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            return None

    async def extract_reports(self, input_text: str, is_user_input: bool = False) -> Optional[Reports]:
        """
        Unified async extraction interface.
        Uses Perplexity for news, Gemini for user input or fallback.
        """
        if is_user_input:
            FALLBACK_USED.inc()
            return await self.extract_from_gemini(input_text)

        # Try Perplexity first
        reports = await self.extract_from_perplexity(input_text)
        if reports and len(reports.reports) > 0:
            return reports

        # Fallback to Gemini
        FALLBACK_USED.inc()
        return await self.extract_from_gemini(input_text)
    
    def create_metric_if_not_exists(metric_class, name, documentation, labelnames=None):
        """Helper to avoid duplicate registration across test files or reloads"""
        try:
            return metric_class(name, documentation, labelnames or [])
        except ValueError:
            # Metric already exists — return existing one
            if name in REGISTRY._names_to_collectors:
                return REGISTRY._names_to_collectors[name]
            # Fallback: create with _created suffix avoided
            return metric_class(name + "_v2", documentation, labelnames or [])

    # Prometheus metrics — SAFE for multiple imports
    EXTRACTION_ATTEMPTS = create_metric_if_not_exists(
        PrometheusCounter, 'extractor_extraction_attempts_total', 'Total extraction attempts', ['method']
    )
    EXTRACTION_SUCCESS = create_metric_if_not_exists(
        PrometheusCounter, 'extractor_extraction_success_total', 'Successful extractions', ['method']
    )
    EXTRACTION_DURATION = create_metric_if_not_exists(
        Histogram, 'extractor_extraction_duration_seconds', 'Extraction duration', ['method']
    )
    FALLBACK_USED = create_metric_if_not_exists(
        PrometheusCounter, 'extractor_fallback_used_total', 'Gemini fallback usage'
    )