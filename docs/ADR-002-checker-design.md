# ADR-002: Checker Agent Design

## Context
Need to deduplicate and verify credibility of incoming disaster reports from heterogeneous sources.

## Decision
- Fuzzy clustering on 4 dimensions: event, location, time, description
- Threshold-based rumor filtering: 2 trusted sources OR 3+ total sources
- Highest-confidence representative per cluster
- Configurable thresholds for tuning per disaster type

## Alternatives Considered
- Vector embeddings + cosine similarity → higher accuracy but slower, needs GPU
- Graph-based clustering → overkill for current scale
- Rule-based only → too rigid for real-world noise

## Consequences
- O(n²) complexity — not scalable beyond 1k reports without indexing
- RapidFuzz dependency — adds C++ compilation requirement
- Time window fixed to 1 hour — may need dynamic adjustment per event type