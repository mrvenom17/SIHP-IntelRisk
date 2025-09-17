# benchmarks/benchmark_analyser.py
import time
from src.analyser.analyser import AnalyserA, Report

def benchmark():
    analyser = AnalyserA()
    reports = [
        Report(event_type="riot", description="Crowd is angry and scared. Police are responding. People are running away in panic.", location=f"City_{i}", timestamp="2025-09-14T12:00:00Z", source="social_media", confidence=0.9)
        for i in range(100)
    ]

    start = time.time()
    output = analyser.analyze_reports(reports)
    end = time.time()

    print(f"Processed {len(reports)} reports in {end - start:.2f}s")
    print(f"Latency per report: {(end - start)/len(reports)*1000:.2f}ms")
    print(f"Total human hotspots: {len(output.human_hotspots)}")

if __name__ == "__main__":
    benchmark()