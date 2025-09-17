# ADR-007: Schema Design

## Context
Need a unified contract between all pipeline components and frontend.

## Decision
- JSON Schema Draft 7 for broad compatibility  
- Versioned schema ($id) for backward compatibility  
- Examples and descriptions for developer onboarding  
- Relaxed required fields for early pipeline stages  
- Strict validation for final map output  

## Alternatives Considered
- Protocol Buffers → faster but less human-readable  
- GraphQL Schema → overkill for data contract  
- TypeScript Interfaces → not language-agnostic  

## Consequences
- Breaking changes require version bump  
- Frontend must handle multiple schema versions during rollout  
- Validation adds ~1ms overhead per object  