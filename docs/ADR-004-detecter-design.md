# ADR-004: Detecter Agent Design

## Context
Need to aggregate human and disaster hotspots into geospatial clusters for real-time map rendering.

## Decision
- Geocode locations using Nominatim (OSM) with 1 req/sec rate limiting  
- DBSCAN clustering with 5km radius (Haversine distance)  
- Weighted centroid calculation using confidence scores  
- Update existing hotspots within 5km to avoid duplication  
- Async implementation for real-time performance  

## Alternatives Considered
- K-means → requires predefined cluster count  
- Hierarchical clustering → O(n²) complexity  
- GeoHash → less accurate for irregular disaster zones  

## Consequences
- Nominatim rate limiting may slow initial processing  
- DBSCAN may create overlapping clusters at boundaries  
- Confidence-weighted centroids may drift with new reports  