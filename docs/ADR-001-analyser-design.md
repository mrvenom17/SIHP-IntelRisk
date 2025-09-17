# ADR-001: Analyser Agent Design

## Context
Need to extract human emotion and disaster severity from unstructured text in real-time.

## Decision
- Use HuggingFace `distilroberta-base` for emotion classification: balance of speed/accuracy
- Sentence-level chunking for granular panic mapping
- Configurable severity/panic weights for tunability
- Async support for web serving
- Prometheus metrics for SLO monitoring

## Alternatives Considered
- spaCy + custom emotion model → slower, heavier
- Google Cloud NLP → cost, latency, vendor lock-in
- Rule-based keyword matching → low accuracy

## Consequences
- Model must be pre-downloaded in Docker
- Panic scoring is heuristic → requires calibration with real data