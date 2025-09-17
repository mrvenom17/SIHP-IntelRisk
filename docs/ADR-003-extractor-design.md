# ADR-003: Extractor Agent Design

## Context
Need to convert unstructured text (news, social, user reports) into structured `Report` objects for downstream agents.

## Decision
- Primary: Perplexity API (web-augmented, real-time)  
- Fallback: Gemini 1.5 Flash (lower cost, faster)  
- Input sanitization to prevent prompt injection  
- Async with retries for resilience  
- Post-processing for veracity/confidence tuning  

## Alternatives Considered
- Fine-tuned local LLM → higher latency, no web context  
- Rule-based regex → too brittle for real-world text  
- OpenAI GPT-4 → higher cost, no significant accuracy gain  

## Consequences
- Dependency on external APIs → need fallbacks and circuit breakers  
- Cost scales with volume → implement caching layer later  
- Gemini requires Google API key → secret management critical  