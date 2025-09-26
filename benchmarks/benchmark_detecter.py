# benchmarks/benchmark_detecter.py
import asyncio
import time
from unittest.mock import MagicMock
from src.detecter.detecter import DetecterA

async def benchmark():
    # Mock DB session
    mock_session = MagicMock()
    mock_session.execute = MagicMock(return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: [])))
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()

    detecter = DetecterA(mock_session)

    # Mock hotspots
    class MockHotspot:
        def __init__(self, lat, lon):
            self.location = "Test Location"
            self.confidence = 1.0
            self.report_id = 1
            self.emotions = [{"emotion": "fear", "score": 0.8}]
            self.panic_level = "high"
            self.event_type = "flood"
            self.severity = "high"
            self.risk_level = "high"
            self.status = "pending"

    humans = [MockHotspot(40.7128 + i*0.01, -74.0060 + i*0.01) for i in range(50)]
    disasters = [MockHotspot(40.7128 + i*0.01, -74.0060 + i*0.01) for i in range(50)]

    with patch('src.detecter.detecter.GeoCoder.geocode', return_value=(40.7128, -74.0060)):
        start = time.time()
        result = await detecter.generate_map_json_with_persistence()
        end = time.time()

    print(f"Processed 100 hotspots in {end - start:.2f}s")
    print(f"Generated {len(result)} composite hotspots")