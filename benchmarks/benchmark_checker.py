# benchmarks/benchmark_checker.py
import time
import random
import string
from src.checker.checker import CheckerA, Report

def generate_report(i: int) -> Report:
    event_types = ["fire", "flood", "earthquake", "riot"]
    locations = ["Paris", "London", "Tokyo", "New York"]
    return Report(
        event_type=random.choice(event_types),
        location=random.choice(locations),
        timestamp=f"2025-09-14T12:{random.randint(0,59):02d}:00Z",
        description=''.join(random.choices(string.ascii_letters + ' ', k=50)),
        source="twitter" if i % 3 else "official_news_agency",
        confidence=random.uniform(0.5, 1.0)
    )

def benchmark():
    checker = CheckerA()
    reports = [generate_report(i) for i in range(500)]  # Simulate 500 reports

    start = time.time()
    verified = checker.run(reports)
    end = time.time()

    print(f"Processed {len(reports)} reports in {end - start:.2f}s")
    print(f"Verified {len(verified)} reports")
    print(f"Throughput: {len(reports)/(end-start):.2f} reports/sec")

if __name__ == "__main__":
    benchmark()