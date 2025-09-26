# benchmarks/benchmark_agents.py
import asyncio
import time
import json
from pathlib import Path

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.extractor.extractor import ExtractorA
from src.checker.checker import CheckerA, Report as CheckerReport
from src.analyser.analyser import AnalyserA, Report as AnalyserReport
from src.detecter.detecter import DetecterA, GeoCoder

# Sample data
SAMPLE_TEXTS = [
    "Heavy flooding reported in Chennai last night. Water levels rising rapidly.",
    "Tsunami warning issued for Andaman coast. Evacuate immediately.",
    "High waves damaging fishing boats in Puri. Local fishermen stranded.",
    "False alarm: No tsunami in Kerala. Officials confirm all clear.",
    "Social media panic: 'Tsunami coming to Mumbai!' — but no official warning.",
    "Storm surge expected in Odisha. Coastal residents advised to move inland.",
    "Unusual tides observed in Goa. Tourists advised to stay away from beaches.",
    "Coastal erosion worsening in Tamil Nadu. Homes at risk.",
    "Fishermen report abnormal currents near Lakshadweep. Navigation difficult.",
    "Crowd panic in Visakhapatnam as sirens go off. No official statement yet."
]

# Mock ORM-like classes (since we're not using real DB)
class MockHumanHotspot:
    def __init__(self, location, timestamp, emotions, panic_level, confidence):
        self.location = location
        self.timestamp = timestamp
        self.emotions = emotions
        self.panic_level = panic_level
        self.confidence = confidence
        self.status = "pending"
        self.report_id = 1  # dummy

class MockDisasterHotspot:
    def __init__(self, location, timestamp, event_type, severity, risk_level, confidence):
        self.location = location
        self.timestamp = timestamp
        self.event_type = event_type
        self.severity = severity
        self.risk_level = risk_level
        self.confidence = confidence
        self.status = "pending"
        self.report_id = 1  # dummy

async def benchmark_extractor():
    extractor = ExtractorA()
    print("=== Benchmarking ExtractorA ===")
    
    start_time = time.time()
    results = []
    
    for text in SAMPLE_TEXTS:
        try:
            result = await extractor.extract_reports(text, is_user_input=False)
            if result and result.reports:
                results.extend(result.reports)
                print(f"✅ Extracted {len(result.reports)} reports from: {text[:50]}...")
            else:
                print(f"⚠️ No reports extracted from: {text[:50]}...")
        except Exception as e:
            print(f"❌ Extraction failed for '{text[:50]}...': {e}")
    
    end_time = time.time()
    print(f"\nProcessed {len(SAMPLE_TEXTS)} texts in {end_time - start_time:.2f}s")
    print(f"Total reports extracted: {len(results)}")
    return results

def benchmark_checker(reports):
    print("\n=== Benchmarking CheckerA ===")
    
    start_time = time.time()
    checker_reports = [
        CheckerReport(
            event_type=r.event_type,
            location=r.location,
            timestamp=r.timestamp,
            description=r.description,
            source=r.source,
            media_urls=r.media_urls or [],
            reporter=r.reporter,
            confidence=r.confidence,
            veracity_flag=r.veracity_flag,
        )
        for r in reports
    ]
    
    checker = CheckerA()
    verified = checker.run(checker_reports)
    
    end_time = time.time()
    print(f"Processed {len(reports)} reports in {end_time - start_time:.2f}s")
    print(f"Verified reports: {len(verified)}")
    return verified

async def benchmark_analyser(reports):
    print("\n=== Benchmarking AnalyserA ===")
    
    analyser = AnalyserA()
    start_time = time.time()
    human_hotspots = []
    disaster_hotspots = []
    
    for report in reports:
        pydantic_report = AnalyserReport(
            event_type=report.event_type,
            location=report.location,
            timestamp=report.timestamp,
            description=report.description,
            source=report.source,
            confidence=report.confidence,
        )
        analysis = await analyser.analyze_reports_async([pydantic_report])
        # Convert to mock ORM objects
        for h in analysis.human_hotspots:
            human_hotspots.append(MockHumanHotspot(
                location=h.location,
                timestamp=h.timestamp,
                emotions=[e.dict() for e in h.emotions],
                panic_level=h.panic_level,
                confidence=h.confidence,
            ))
        for d in analysis.disaster_hotspots:
            disaster_hotspots.append(MockDisasterHotspot(
                location=d.location,
                timestamp=d.timestamp,
                event_type=d.event_type,
                severity=d.severity,
                risk_level=d.risk_level,
                confidence=d.confidence,
            ))
    
    end_time = time.time()
    print(f"Processed {len(reports)} reports in {end_time - start_time:.2f}s")
    print(f"Human hotspots: {len(human_hotspots)}")
    print(f"Disaster hotspots: {len(disaster_hotspots)}")
    return human_hotspots, disaster_hotspots

def benchmark_detecter(human_hotspots, disaster_hotspots):
    print("\n=== Benchmarking DetecterA ===")
    
    # Mock DB — just a list
    class MockDB:
        def __init__(self):
            self.composite_hotspots = []
        async def commit(self): pass
        async def refresh(self, obj): pass
    
    # Mock geocoding — always return Chennai
    mock_geocoder = GeoCoder()
    mock_geocoder.geocode = lambda loc: (13.0827, 80.2707)  # Chennai
    
    detecter = DetecterA(MockDB())
    detecter.geocoder = mock_geocoder  # Override with mock
    
    start_time = time.time()
    
    # Assemble points directly from mock ORM objects
    points = []
    for h in human_hotspots:
        coords = detecter.geocoder.geocode(h.location)
        if coords:
            points.append({
                "type": "human",
                "payload": h,
                "latitude": coords[0],
                "longitude": coords[1],
                "confidence": h.confidence or 1.0,
            })
    for d in disaster_hotspots:
        coords = detecter.geocoder.geocode(d.location)
        if coords:
            points.append({
                "type": "disaster",
                "payload": d,
                "latitude": coords[0],
                "longitude": coords[1],
                "confidence": d.confidence or 1.0,
            })
    
    if not points:
        print("❌ No geocoded points found")
        return []
    
    # Cluster and process
    clusters = detecter.cluster_points(points)
    output_list = []
    for cluster_points in clusters.values():
        try:
            hotspot_data = asyncio.run(detecter.update_or_create_composite_hotspot(cluster_points))
            output_list.append(hotspot_data)
        except Exception as e:
            print(f"❌ Failed to process cluster: {e}")
            continue
    
    # Mark as aggregated (mock)
    for p in points:
        p["payload"].status = "aggregated"
    
    end_time = time.time()
    print(f"Processed {len(points)} points in {end_time - start_time:.2f}s")
    print(f"Composite hotspots: {len(output_list)}")
    return output_list

async def main():
    print("🚀 Starting Agent Benchmark with Real LLM APIs...\n")
    
    # 1. Extract
    extracted_reports = await benchmark_extractor()
    if not extracted_reports:
        print("❌ No reports extracted. Check API keys and network.")
        return
    
    # 2. Check
    verified_reports = benchmark_checker(extracted_reports)
    if not verified_reports:
        print("❌ No reports verified. Adjust CheckerA thresholds if needed.")
        return
    
    # 3. Analyse
    human_hotspots, disaster_hotspots = await benchmark_analyser(verified_reports)
    if not human_hotspots and not disaster_hotspots:
        print("❌ No hotspots generated. Check AnalyserA model loading.")
        return
    
    # 4. Detect
    composite_hotspots = benchmark_detecter(human_hotspots, disaster_hotspots)
    
    print("\n🎉 Benchmark Complete!")
    print(f"Final Output: {len(composite_hotspots)} composite hotspots")
    if composite_hotspots:
        print("\nSample Composite Hotspot:")
        print(json.dumps(composite_hotspots[0], indent=2))

if __name__ == "__main__":
    asyncio.run(main())