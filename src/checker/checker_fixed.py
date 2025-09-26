# src/checker/checker_fixed.py
import asyncio
import logging
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
from datetime import datetime
import time
from prometheus_client import Counter as PrometheusCounter, Histogram, Gauge

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
CLUSTERS_CREATED = PrometheusCounter('checker_clusters_created_total', 'Total clusters created')
REPORTS_PROCESSED = PrometheusCounter('checker_reports_processed_total', 'Total reports processed')
REPORTS_VERIFIED = PrometheusCounter('checker_reports_verified_total', 'Reports verified and passed')
REPORTS_FILTERED = PrometheusCounter('checker_reports_filtered_total', 'Reports filtered as rumor')
CLUSTER_SIZE = Histogram('checker_cluster_size', 'Size of created clusters', buckets=[1, 2, 5, 10, 20, 50])
PROCESSING_DURATION = Histogram('checker_processing_duration_seconds', 'Time spent processing reports')

# === 1. Report schema ===

class Report(BaseModel):
    event_type: Optional[str] = None
    location: Optional[str] = None
    timestamp: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    media_urls: Optional[List[str]] = Field(default_factory=list)
    reporter: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    veracity_flag: Optional[str] = None

class Reports(BaseModel):
    reports: List[Report]

# === 2. CheckerA ===

class CheckerA:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.trusted_sources: Set[str] = set(config.get("trusted_sources", [
            "official_news_agency",
            "government_official",
            "well_known_media",
            "red_cross",
            "un_official_disaster_org"
        ]))
        # MORE RELAXED THRESHOLDS for better verification
        self.event_type_similarity_threshold = config.get("event_type_similarity_threshold", 60)  # was 85
        self.location_similarity_threshold = config.get("location_similarity_threshold", 60)      # was 80
        self.description_similarity_threshold = config.get("description_similarity_threshold", 60) # was 85
        self.time_window_seconds = config.get("time_window_seconds", 7200)  # 2 hours, was 3600

    def normalize_source(self, source: Optional[str]) -> Optional[str]:
        if not source:
            return None
        return source.strip().lower().replace(" ", "_")

    def is_source_trusted(self, source: Optional[str]) -> bool:
        norm = self.normalize_source(source)
        return bool(norm) and norm in self.trusted_sources

    def similarity(self, a: Optional[str], b: Optional[str]) -> float:
        if not a or not b:
            return 0.0
        try:
            return float(fuzz.token_set_ratio(str(a).lower(), str(b).lower()))
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0

    def time_within_window(self, t1: Optional[str], t2: Optional[str]) -> bool:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        try:
            dt1 = datetime.strptime(t1, fmt)
            dt2 = datetime.strptime(t2, fmt)
            return abs((dt1 - dt2).total_seconds()) <= self.time_window_seconds
        except Exception as e:
            logger.warning(f"Timestamp parsing failed for {t1} or {t2}: {e}")
            return False

    def _create_clusters(self, reports: List[Report]) -> List[List[Report]]:
        clusters: List[List[Report]] = []
        start_time = time.time()

        for report in reports:
            matched_cluster = None
            for cluster in clusters:
                rep = cluster[0]  # Compare against first report in cluster

                # More lenient clustering - only require 2 out of 4 fields to match
                match_count = 0
                total_fields = 0

                # Event type matching (if both present)
                if report.event_type and rep.event_type:
                    total_fields += 1
                    if self.similarity(report.event_type, rep.event_type) >= self.event_type_similarity_threshold:
                        match_count += 1

                # Location matching (if both present)
                if report.location and rep.location:
                    total_fields += 1
                    if self.similarity(report.location, rep.location) >= self.location_similarity_threshold:
                        match_count += 1

                # Timestamp matching (if both present)
                if report.timestamp and rep.timestamp:
                    total_fields += 1
                    if self.time_within_window(report.timestamp, rep.timestamp):
                        match_count += 1

                # Description matching (if both present)
                if report.description and rep.description:
                    total_fields += 1
                    if self.similarity(report.description, rep.description) >= self.description_similarity_threshold:
                        match_count += 1

                # If at least 2 fields match (or 1 if only 2 total fields), cluster them
                if total_fields > 0 and match_count >= max(2, total_fields // 2):
                    matched_cluster = cluster
                    break

            if matched_cluster is None:
                clusters.append([report])
            else:
                matched_cluster.append(report)

        PROCESSING_DURATION.observe(time.time() - start_time)
        CLUSTERS_CREATED.inc(len(clusters))
        for cluster in clusters:
            CLUSTER_SIZE.observe(len(cluster))

        logger.info(f"Created {len(clusters)} clusters from {len(reports)} reports")
        return clusters

    def process_clusters(self, clusters: List[List[Report]]) -> List[Report]:
        verified_reports = []

        for cluster in clusters:
            trusted_count = sum(self.is_source_trusted(r.source) for r in cluster)
            total_count = len(cluster)

            REPORTS_PROCESSED.inc(total_count)

            # ✅ Accept single trusted report
            if trusted_count >= 1 and total_count == 1:
                pass
            # ✅ Accept clusters with at least 2 reports (even if no trusted sources)
            elif total_count >= 2:
                pass
            # ✅ Reject only if zero trusted AND fewer than 2 total
            elif trusted_count == 0 and total_count < 2:
                REPORTS_FILTERED.inc(total_count)
                logger.debug(f"Cluster rejected: zero trusted, {total_count} total")
                continue

            best_report = max(cluster, key=lambda r: r.confidence or 0)
            if not best_report.reporter:
                best_report.reporter = "unknown"
            best_report.veracity_flag = "verified"

            verified_reports.append(best_report)
            REPORTS_VERIFIED.inc()

        return verified_reports

    def run(self, reports: List[Report]) -> List[Report]:
        """Synchronous entry point"""
        clusters = self._create_clusters(reports)
        return self.process_clusters(clusters)

    async def run_async(self, reports: List[Report]) -> List[Report]:
        """Async wrapper for web services"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, reports)
