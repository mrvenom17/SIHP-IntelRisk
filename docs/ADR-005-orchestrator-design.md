# ADR-005: Orchestrator Design

## Context
Need to coordinate Extractor → Checker → Analyser → Detecter agents reliably at scale.

## Decision
- Redis Streams for message passing: persistence, consumer groups, exactly-once  
- Async workers with retry logic  
- Prometheus for metrics  
- FastAPI for REST endpoints  
- Scheduled Detecter runs every 5min (batch optimization)  

## Alternatives Considered
- Kafka → heavier, needs ZooKeeper  
- RabbitMQ → no built-in persistence  
- Celery → overkill for linear pipeline  

## Consequences
- Redis becomes critical path — need HA setup  
- Workers must be stateless for horizontal scaling  
- 5min Detecter delay acceptable for disaster response  