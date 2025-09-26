# src/extractor/extractor_fixed.py
import asyncio
import logging
import re
import json
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from prometheus_client import Counter as PrometheusCounter, Histogram, REGISTRY
import time
from datetime import datetime, timedelta, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# FIXED: Removed trailing spaces
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

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

# === 4. Prompts for Extraction ===

from langchain.prompts import ChatPromptTemplate

GEMINI_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a disaster events extractor. Extract each distinct event into a report.\n"
    "Return ONLY a VALID JSON object with key 'reports' containing list of reports.\n"
    "SCHEMA: Report fields: event_type, location, timestamp, description, source, media_urls, reporter, confidence, veracity_flag\n"
    "EXAMPLE: {\"reports\": [{\"event_type\": \"flood\", \"location\": \"Chennai\", \"description\": \"Heavy rains\", \"source\": \"news\", \"confidence\": 0.9, \"veracity_flag\": \"confirmed\"}]}\n"
    "DO NOT USE MARKDOWN. DO NOT ADD COMMENTS. ONLY RETURN JSON.\n"
    "Input text: {text}"
)

PERPLEXITY_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    "You are a disaster intelligence system. Extract structured data from the text below.\n"
    "Identify: event_type, location, timestamp (ISO8601 or null), description, source, confidence (0-1), veracity_flag.\n"
    "RETURN ONLY A VALID JSON OBJECT WITH KEY 'reports' CONTAINING A LIST OF REPORT OBJECTS.\n"
    "EXAMPLE: {\"reports\": [{\"event_type\": \"flood\", \"location\": \"Chennai\", \"description\": \"Heavy rains\", \"source\": \"news\", \"confidence\": 0.9, \"veracity_flag\": \"confirmed\"}]}\n"
    "DO NOT ADD MARKDOWN. DO NOT ADD COMMENTS. ONLY RETURN JSON.\n"
    "Text: {text}"
)

# === 5. Helper Functions ===

def create_metric_if_not_exists(metric_class, name, documentation, labelnames=None):
    """Helper to avoid duplicate registration across test files or reloads"""
    try:
        return metric_class(name, documentation, labelnames or [])
    except ValueError:
        # Metric already exists — return existing one
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        # Fallback: create with _v2 suffix
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

# === 6. Extractor Class ===

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

    def sanitize_input(self, text: str) -> str:
        """Prevent prompt injection and control chars"""
        if not text:
            return ""
        # Remove control chars except \n\t
        sanitized = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')
        # Escape curly braces that might break JSON
        sanitized = sanitized.replace("{", "{{").replace("}", "}}")
        return sanitized[:5000]  # Limit input length

    def normalize_relative_times(self, text: str, reference_date: Optional[datetime] = None) -> str:
        if not reference_date:
            reference_date = datetime.now(timezone.utc)

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

    def _clean_llm_json_output(self, text: str) -> str:
        """Remove Markdown code fences and clean JSON string"""
        if not text:
            return ""

        # Strip ```json ... ``` or ``` ... ```
        if text.strip().startswith('```'):
            start = text.find('```')
            end = text.rfind('```', start + 3)
            if end != -1:
                text = text[start + 3:end]
                # Remove optional "json" after opening ```
                text = text.lstrip('json').lstrip()

        # Remove any remaining control characters except \n\t
        text = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')

        return text.strip()

    async def extract_from_perplexity(self, query: str) -> Optional[Reports]:
        if not PERPLEXITY_API_KEY or PERPLEXITY_API_KEY.strip() == "":
            logger.warning("Perplexity API key missing; skipping extraction.")
            return None

        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
        normalized_text = self.normalize_relative_times(query)
        prompt_text = PERPLEXITY_PROMPT_TEMPLATE.format(text=normalized_text)
        payload = {
            "model": "sonar-pro",
            "messages": [
                {"role": "user", "content": prompt_text}
            ]
        }
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=15)
            )
            response.raise_for_status()
            data = response.json()

            raw_json_str = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.debug(f"Perplexity raw output: {raw_json_str[:500]}...")
            if not raw_json_str:
                logger.warning("Perplexity returned empty content")
                return None

            # Clean and parse
            clean_json_str = self._clean_llm_json_output(raw_json_str)
            if not clean_json_str:
                logger.warning("Cleaned JSON is empty")
                return None

            try:
                reports = Reports.model_validate_json(clean_json_str)
                logger.info(f"✅ Perplexity extracted {len(reports.reports)} reports")
                return self.post_process_reports(reports)
            except ValidationError as e:
                logger.warning(f"Perplexity JSON validation failed: {e}")
                logger.debug(f"Failed JSON: {clean_json_str}")

                # Fallback: Create single report from plain text
                logger.info("🔧 Creating single report from plain text")
                single_report = {
                    "reports": [{
                        "event_type": self._infer_event_type(clean_json_str),
                        "location": self._infer_location(clean_json_str),
                        "description": clean_json_str[:500],
                        "source": "perplexity",
                        "confidence": 0.8,
                        "veracity_flag": "confirmed"
                    }]
                }
                try:
                    reports = Reports.model_validate_json(json.dumps(single_report))
                    logger.info("✅ Created fallback report from plain text")
                    return self.post_process_reports(reports)
                except Exception as e2:
                    logger.error(f"Failed to create fallback report: {e2}")
                    return Reports(reports=[])

        except Exception as e:
            logger.error(f"Perplexity extraction error: {e}")
            return None

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
        # Expand this list with more locations
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

    async def extract_from_gemini(self, text: str) -> Optional[Reports]:
        """Async Gemini extraction with JSON cleaning"""
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
                content = gemini_response.content
                if isinstance(content, str):
                    raw_json_str = content
                elif isinstance(content, list):
                    # Handle list content by joining
                    raw_json_str = " ".join(str(item) for item in content if item)
                else:
                    raw_json_str = str(content)
            elif isinstance(gemini_response, str):
                raw_json_str = gemini_response
            else:
                raw_json_str = str(gemini_response)

            # CLEAN THE OUTPUT
            clean_json_str = self._clean_llm_json_output(raw_json_str)
            logger.debug(f"Cleaned JSON: {clean_json_str[:200]}...")

            if not clean_json_str:
                logger.warning("Empty response after cleaning")
                return Reports(reports=[])

            # After cleaning, try to parse:
            try:
                reports = Reports.model_validate_json(clean_json_str)
                logger.info(f"✅ Gemini extracted {len(reports.reports)} reports")
                return self.post_process_reports(reports)
            except ValidationError as e:
                logger.warning(f"Gemini JSON validation failed: {e}")
                try:
                    obj = json.loads(clean_json_str)
                    if isinstance(obj, list):
                        wrapped = {"reports": obj}
                        reports = Reports.model_validate(wrapped)
                        logger.info(f"✅ Gemini extracted {len(reports.reports)} reports (wrapped)")
                        return self.post_process_reports(reports)
                    elif isinstance(obj, dict) and "reports" in obj:
                        reports = Reports.model_validate(obj)
                        logger.info(f"✅ Gemini extracted {len(reports.reports)} reports (dict)")
                        return self.post_process_reports(reports)
                except Exception as e2:
                    logger.warning(f"Gemini fallback parsing failed: {e2}")

                # Final fallback: Create single report from plain text
                logger.info("🔧 Creating single report from plain text (Gemini)")
                single_report = {
                    "reports": [{
                        "event_type": self._infer_event_type(clean_json_str),
                        "location": self._infer_location(clean_json_str),
                        "description": clean_json_str[:500],
                        "source": "gemini",
                        "confidence": 0.7,
                        "veracity_flag": "confirmed"
                    }]
                }
                try:
                    reports = Reports.model_validate_json(json.dumps(single_report))
                    logger.info("✅ Created fallback report from plain text (Gemini)")
                    return self.post_process_reports(reports)
                except Exception as e3:
                    logger.error(f"Failed to create fallback report (Gemini): {e3}")
                    return Reports(reports=[])

        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            return None

    async def extract_reports(self, input_text: str, is_user_input: bool = False) -> Optional[Reports]:
        """
        Extracts disaster reports using Perplexity API as primary source,
        falling back to Gemini model only if Perplexity fails or returns no reports.
        """
        logger.info("🔍 Using Perplexity as primary extractor")
        reports = await self.extract_from_perplexity(input_text)
        if reports and len(reports.reports) > 0:
            logger.info(f"✅ Perplexity extracted {len(reports.reports)} reports")
            return reports
        else:
            logger.warning("⚠️ Perplexity returned no reports — falling back to Gemini")
            logger.info("🔍 Using Gemini as fallback extractor")
            return await self.extract_from_gemini(input_text)
