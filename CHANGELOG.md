# Changelog

## [1.0.0] - 2025-04-05
### Added
- Production-ready AnalyserA with async, metrics, error handling
- Unit + integration tests
- Docker + CI/CD
- Input sanitization and panic score histogram

### Changed
- Moved NLTK download to Docker build
- Added configurable severity/panic maps
- Added Prometheus metrics

### Fixed
- Crash on empty text
- Global model loading

## [1.1.0] - 2025-04-05
### Added
- Production-ready CheckerA with async support, metrics, logging
- Configurable thresholds and trusted sources
- Veracity flag on output reports
- Property-based tests for clustering logic

### Changed
- Removed duplicate time_within_window function
- Replaced sys.path hack with proper package structure
- Added error handling for timestamp parsing and similarity

### Fixed
- Crash on non-string fields
- Silent failures in timestamp parsing

## [1.2.0] - 2025-04-05
### Added
- Production-ready ExtractorA with async, retries, metrics
- Input sanitization and prompt injection protection
- Thread-safe Gemini initialization
- Contract tests with mocked APIs

### Changed
- Fixed Perplexity API URL (removed trailing spaces)
- Replaced prints with structured logging
- Added exponential backoff for API calls

### Fixed
- Race condition in Gemini initialization
- JSON validation failures not crashing pipeline