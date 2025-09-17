# benchmarks/benchmark_extractor.py
import asyncio
import time
from src.extractor.extractor import ExtractorA

async def benchmark():
    extractor = ExtractorA()
    texts = [
        "Flood in Jakarta last night submerged 3 neighborhoods",
        "Wildfire near LA spreading rapidly, evacuations ordered",
        "Riot in Paris downtown, police deployed",
    ] * 10  # 30 extractions

    start = time.time()
    tasks = [extractor.extract_reports(text) for text in texts]
    results = await asyncio.gather(*tasks)
    end = time.time()

    successful = sum(1 for r in results if r and len(r.reports) > 0)
    print(f"Processed {len(texts)} extractions in {end - start:.2f}s")
    print(f"Success rate: {successful}/{len(texts)}")
    print(f"Latency per extraction: {(end - start)/len(texts)*1000:.2f}ms")

if __name__ == "__main__":
    asyncio.run(benchmark())