# ADR-006: Database Schema Design

## Context
Need to store state for 4-stage agent pipeline with relationships between entities.

## Decision
- Normalized schema with foreign keys  
- Indexes on all agent query fields (status, location, timestamp)  
- Geospatial composite index on latitude/longitude  
- Async-compatible SQLAlchemy models  
- M:N relationship for composite hotspots ← reports  

## Alternatives Considered
- NoSQL (MongoDB) → harder to enforce relationships  
- Graph DB (Neo4j) → overkill for linear pipeline  
- Denormalized → data consistency challenges  

## Consequences
- Schema migrations required for changes (Alembic)  
- Indexes increase write overhead — acceptable for read-heavy workload  
- Cascade deletes simplify cleanup but require careful testing  