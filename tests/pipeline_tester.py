# tests/pipeline_tester.py
import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from pydantic import BaseModel

# Import your app
from src.orchestrator.main import app

# === 1. MOCK MODELS ===

class MockRawPost(BaseModel):
    id: int = 1
    content: Dict[str, str]
    hash: str = "mock_hash_1"
    prev_hash: Optional[str] = None
    timestamp: datetime = datetime.now(timezone.utc)
    status: str = "pending"

class MockReport(BaseModel):
    id: int = 1
    raw_post_id: int = 1
    event_type: Optional[str] = None
    location: Optional[str] = None
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    source: Optional[str] = None
    media_urls: List[str] = []
    reporter: Optional[str] = None
    confidence: Optional[float] = None
    veracity_flag: Optional[str] = None
    status: str = "pending"

class MockHumanHotspot(BaseModel):
    id: int = 1
    report_id: int = 1
    location: Optional[str] = None
    timestamp: Optional[datetime] = None
    emotions: List[Dict[str, Any]] = []
    panic_level: Optional[str] = None
    confidence: float = 0.8
    status: str = "pending"

class MockDisasterHotspot(BaseModel):
    id: int = 1
    report_id: int = 1
    location: Optional[str] = None
    timestamp: Optional[datetime] = None
    event_type: Optional[str] = None
    severity: str = "low"
    risk_level: Optional[str] = None
    confidence: float = 0.9
    status: str = "pending"

class MockCompositeHotspot(BaseModel):
    id: int = 1
    latitude: float = 0.0
    longitude: float = 0.0
    aggregated_emotions: Dict[str, float] = {}
    average_panic_level: float = 0.0
    event_types: List[str] = []
    severity_level: str = "low"
    risk_level: str = "unknown"
    contributing_reports_count: int = 1
    created_at: datetime = datetime.now(timezone.utc)

# === 2. MOCK DATABASE SESSION ===

class MockAsyncSession:
    def __init__(self):
        self.reports = {}
        self.human_hotspots = {}
        self.disaster_hotspots = {}
        self.composite_hotspots = {}
        self.raw_posts = {}
        self.next_id = 1

    async def execute(self, *args, **kwargs):
        class MockResult:
            def __init__(self, data):
                self.data = data

            def scalars(self):
                return self

            def all(self):
                return self.data

            def first(self):
                return self.data[0] if self.data else None

            def scalar(self):
                return self.data[0] if self.data else None

        # Mock queries based on args
        if "SELECT" in str(args):
            return MockResult([])

        if "raw_posts" in str(args):
            return MockResult(list(self.raw_posts.values()))

        if "reports" in str(args):
            status = kwargs.get("status", "pending")
            veracity_flag = kwargs.get("veracity_flag", None)
            filtered = [
                r for r in self.reports.values()
                if r.status == status and (not veracity_flag or r.veracity_flag == veracity_flag)
            ]
            return MockResult(filtered)

        if "human_hotspots" in str(args):
            return MockResult(list(self.human_hotspots.values()))

        if "disaster_hotspots" in str(args):
            return MockResult(list(self.disaster_hotspots.values()))

        return MockResult([])

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    def add(self, obj):
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = self.next_id
            self.next_id += 1

        if isinstance(obj, MockRawPost):
            self.raw_posts[obj.id] = obj
        elif isinstance(obj, MockReport):
            self.reports[obj.id] = obj
        elif isinstance(obj, MockHumanHotspot):
            self.human_hotspots[obj.id] = obj
        elif isinstance(obj, MockDisasterHotspot):
            self.disaster_hotspots[obj.id] = obj
        elif isinstance(obj, MockCompositeHotspot):
            self.composite_hotspots[obj.id] = obj

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# === 3. MOCK REDIS ===

class MockRedis:
    def __init__(self):
        self.streams = {
            "raw_posts": [],
            "reports_to_check": [],
            "analyzed_reports": []
        }
        self.groups = {}

    async def xadd(self, stream, data):
        self.streams[stream].append(data)
        print(f"[MOCK REDIS] Added to {stream}: {data}")

    async def xreadgroup(self, group, consumer, streams, count=20, block=5000):
        results = []
        for stream_name, _ in streams.items():
            if stream_name in self.streams and self.streams[stream_name]:
                events = []
                for i, data in enumerate(self.streams[stream_name][:count]):
                    event_id = f"event_{i}"
                    events.append((event_id, data))
                if events:
                    results.append((stream_name, events))
                # Clear processed (simplified)
                self.streams[stream_name] = self.streams[stream_name][count:]
        return results

    async def xack(self, stream, group, event_id):
        pass

    async def xgroup_create(self, stream, group, id="0", mkstream=True):
        self.groups[group] = {"stream": stream, "last_id": id}

    async def ping(self):
        return True

# === 4. MOCK EXTRACTOR ===

class MockExtractorA:
    @staticmethod
    async def extract_reports(input_text: str, is_user_input: bool = False) -> Any:
        # Mock extraction - create simple report
        from src.extractor.extractor import Reports, Report as ExtractorReport
        return Reports(reports=[
            ExtractorReport(
                event_type="flood" if "flood" in input_text.lower() else "fire",
                location="Jakarta" if "jakarta" in input_text.lower() else "Los Angeles",
                timestamp="2025-04-05T12:00:00Z",
                description=input_text[:200],
                source="mock_news",
                confidence=0.85,
                veracity_flag="confirmed",
                media_urls=[],
                reporter="mock_reporter"
            )
        ])

# === 5. MOCK CHECKER ===

class MockCheckerA:
    def __init__(self, reports=None):
        pass

    async def run_async(self, reports):
        # Return all reports as verified (simplified)
        from src.checker.checker import Report as CheckerReport
        return [CheckerReport(**r.dict()) for r in reports] if reports else []

# === 6. MOCK ANALYSER ===

class MockAnalyserA:
    async def analyze_reports_async(self, reports):
        from src.analyser.analyser import AnalysisOutput, HumanHotspot as AnalyserHumanHotspot, DisasterHotspot as AnalyserDisasterHotspot, EmotionScore
        human_hotspots = []
        disaster_hotspots = []

        for report in reports:
            # Mock human hotspot
            human_hotspots.append(
                AnalyserHumanHotspot(
                    location=report.location,
                    timestamp=report.timestamp,
                    emotions=[
                        EmotionScore(emotion="fear", score=0.9),
                        EmotionScore(emotion="sadness", score=0.6)
                    ],
                    panic_level="high",
                    affected_population_estimate=None
                )
            )

            # Mock disaster hotspot
            disaster_hotspots.append(
                AnalyserDisasterHotspot(
                    location=report.location,
                    timestamp=report.timestamp,
                    event_type=report.event_type,
                    severity="high",
                    risk_level="high",
                    description_summary=report.description[:100] if report.description else None
                )
            )

        return AnalysisOutput(
            human_hotspots=human_hotspots,
            disaster_hotspots=disaster_hotspots
        )

# === 7. MOCK DETECTER ===

class MockDetecterA:
    def __init__(self, db_session):
        self.db = db_session

    async def generate_map_json_with_persistence(self):
        from src.detecter.detecter import CompositeHotspotOutput
        # Mock composite hotspot
        return [
            CompositeHotspotOutput(
                latitude=-6.2088,
                longitude=106.8456,
                aggregated_emotions={"fear": 0.85, "sadness": 0.62},
                average_panic_level=0.78,
                event_types=["flood"],
                severity_level="high",
                risk_level="high",
                contributing_reports=5
            )
        ]

# === 8. DEPENDENCY OVERRIDES ===

async def mock_get_db():
    return MockAsyncSession()

def override_extractor():
    return MockExtractorA()

def override_checker():
    return MockCheckerA()

def override_analyser():
    return MockAnalyserA()

# === 9. TEST CLIENT WITH OVERRIDES ===

client = TestClient(app)

# Override dependencies
app.dependency_overrides[MockExtractorA] = override_extractor
app.dependency_overrides[MockCheckerA] = lambda: MockCheckerA()
app.dependency_overrides[MockAnalyserA] = lambda: MockAnalyserA()

# Mock modules
with patch('src.orchestrator.main.ExtractorA', MockExtractorA), \
     patch('src.orchestrator.main.CheckerAgent', MockCheckerA), \
     patch('src.orchestrator.main.AnalyserAgent', MockAnalyserA), \
     patch('src.orchestrator.main.DetecterA', MockDetecterA), \
     patch('src.orchestrator.main.redis', MockRedis()), \
     patch('src.orchestrator.main.get_db', mock_get_db):

    # === 10. PIPELINE TEST FUNCTION ===

    def test_full_pipeline():
        print("\n" + "="*60)
        print("🚀 STARTING FULL PIPELINE TEST")
        print("="*60)

        # Step 1: Ingest raw text
        print("\n📥 STEP 1: Ingesting raw posts...")
        raw_texts = [
            "Major flood in Jakarta submerged downtown areas. People are terrified!",
            "Wildfire spreading rapidly in Los Angeles hills. Evacuations ordered.",
            "Riot in downtown Paris after protest turned violent. Police deployed."
        ]

        response = client.post("/api/ingest", json=raw_texts)
        assert response.status_code == 200
        print(f"✅ Ingested {len(raw_texts)} posts")

        # Step 2: Run extractor worker (mocked)
        print("\n🔧 STEP 2: Running extractor (mocked)...")
        # In real app, this runs in background - here we simulate
        mock_db = MockAsyncSession()
        mock_redis = MockRedis()

        for i, text in enumerate(raw_texts):
            # Simulate extractor
            mock_report = MockReport(
                id=i+1,
                raw_post_id=i+1,
                event_type="flood" if "flood" in text else "fire" if "fire" in text else "riot",
                location="Jakarta" if "Jakarta" in text else "Los Angeles" if "Los Angeles" in text else "Paris",
                timestamp=datetime.now(timezone.utc),
                description=text,
                source="mock_news",
                confidence=0.85,
                veracity_flag="confirmed",
                status="pending"
            )
            mock_db.add(mock_report)
            mock_redis.xadd("reports_to_check", {"report_id": str(mock_report.id)})
            print(f"✅ Extracted report {mock_report.id}: {mock_report.event_type} in {mock_report.location}")

        # Step 3: Run checker worker (mocked)
        print("\n✅ STEP 3: Running checker (mocked)...")
        # Simulate checker - all reports verified
        for i in range(len(raw_texts)):
            report_id = i + 1
            # Update status to processed
            if report_id in mock_db.reports:
                mock_db.reports[report_id].status = "processed"
            mock_redis.xadd("analyzed_reports", {"report_id": str(report_id)})
            print(f"✅ Verified report {report_id}")

        # Step 4: Run analyser worker (mocked)
        print("\n🧠 STEP 4: Running analyser (mocked)...")
        for i in range(len(raw_texts)):
            report_id = i + 1
            if report_id in mock_db.reports:
                report = mock_db.reports[report_id]
                # Create mock human hotspot
                human_hotspot = MockHumanHotspot(
                    id=report_id,
                    report_id=report_id,
                    location=report.location,
                    timestamp=report.timestamp,
                    emotions=[{"emotion": "fear", "score": 0.9}, {"emotion": "anger", "score": 0.7}],
                    panic_level="high",
                    status="pending"
                )
                mock_db.add(human_hotspot)

                # Create mock disaster hotspot
                disaster_hotspot = MockDisasterHotspot(
                    id=report_id,
                    report_id=report_id,
                    location=report.location,
                    timestamp=report.timestamp,
                    event_type=report.event_type,
                    severity="high",
                    risk_level="high",
                    status="pending"
                )
                mock_db.add(disaster_hotspot)
                print(f"✅ Analysed report {report_id}: {report.event_type}")

        # Step 5: Run detecter (mocked)
        print("\n🗺️ STEP 5: Running detecter (mocked)...")
        detecter = MockDetecterA(mock_db)
        composite_hotspots = asyncio.run(detecter.generate_map_json_with_persistence())

        # Mark source hotspots as aggregated
        for h in mock_db.human_hotspots.values():
            h.status = "aggregated"
        for d in mock_db.disaster_hotspots.values():
            d.status = "aggregated"

        print(f"✅ Generated {len(composite_hotspots)} composite hotspots")

        # Step 6: Get map data
        print("\n📡 STEP 6: Fetching map data...")
        map_response = client.get("/api/map/latest")
        assert map_response.status_code == 200
        map_data = map_response.json()
        print(f"✅ Retrieved map with {len(map_data['hotspots'])} hotspots")

        # Step 7: Verify metrics
        print("\n📊 STEP 7: Checking metrics...")
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        print("✅ Metrics endpoint accessible")

        print("\n" + "="*60)
        print("🎉 FULL PIPELINE TEST COMPLETED SUCCESSFULLY!")
        print("="*60)

        return {
            "ingested": len(raw_texts),
            "extracted": len(raw_texts),
            "checked": len(raw_texts),
            "analyzed": len(raw_texts),
            "detected": len(composite_hotspots),
            "map_hotspots": len(map_data['hotspots'])
        }

# === 11. RUN TEST ===

if __name__ == "__main__":
    # Set environment for testing
    os.environ['PERPLEXITY_API_KEY'] = 'mock_key'
    os.environ['GOOGLE_API_KEY'] = 'mock_key'

    # Run the test
    results = test_full_pipeline()

    print("\n📋 TEST SUMMARY:")
    for key, value in results.items():
        print(f"  {key}: {value}")

    print("\n✅ Pipeline tester completed. No DB or Redis required!")