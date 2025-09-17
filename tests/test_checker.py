# tests/test_checker.py
import pytest
from src.checker.checker import CheckerA, Report

@pytest.fixture
def checker():
    return CheckerA()

def test_similarity(checker):
    assert checker.similarity("Fire in Paris", "Fire in Paris") == 100.0
    assert checker.similarity("Fire", "Flood") < 50.0
    assert checker.similarity(None, "Fire") == 0.0

def test_time_within_window(checker):
    t1 = "2025-09-14T12:00:00Z"
    t2 = "2025-09-14T12:30:00Z"
    assert checker.time_within_window(t1, t2) is True

    t3 = "2025-09-14T13:30:00Z"
    assert checker.time_within_window(t1, t3) is False

def test_trusted_source(checker):
    assert checker.is_source_trusted("official_news_agency") is True
    assert checker.is_source_trusted("random_blog") is False

def test_clustering_same_event(checker):
    reports = [
        Report(
            event_type="fire",
            location="Paris",
            timestamp="2025-09-14T12:00:00Z",
            description="Building on fire downtown",
            source="twitter_user",
            confidence=0.7
        ),
        Report(
            event_type="Fire",
            location="paris",
            timestamp="2025-09-14T12:15:00Z",
            description="Building on fire in city center",
            source="official_news_agency",
            confidence=0.9
        )
    ]
    clusters = checker._create_clusters(reports)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2

def test_rumor_filtering(checker):
    # 1 trusted + 1 regular = rejected (needs 2 trusted OR 3 total)
    reports = [
        Report(event_type="riot", location="London", timestamp="2025-09-14T12:00:00Z", description="Protest", source="twitter", confidence=0.6),
        Report(event_type="riot", location="London", timestamp="2025-09-14T12:05:00Z", description="Protest", source="official_news_agency", confidence=0.8),
    ]
    clusters = checker._create_clusters(reports)
    verified = checker.process_clusters(clusters)
    assert len(verified) == 0

def test_verified_cluster(checker):
    reports = [
        Report(event_type="flood", location="Bangkok", timestamp="2025-09-14T12:00:00Z", description="Water rising", source="twitter", confidence=0.5),
        Report(event_type="flood", location="Bangkok", timestamp="2025-09-14T12:10:00Z", description="Water rising fast", source="red_cross", confidence=0.9),
        Report(event_type="flood", location="Bangkok", timestamp="2025-09-14T12:05:00Z", description="Flooding", source="government_official", confidence=0.95),
    ]
    clusters = checker._create_clusters(reports)
    verified = checker.process_clusters(clusters)
    assert len(verified) == 1
    assert verified[0].confidence == 0.95
    assert verified[0].veracity_flag == "verified"

def test_clustering_same_event(checker):
    reports = [
        Report(
            event_type="fire",
            location="Paris",
            timestamp="2025-09-14T12:00:00Z",
            description="Building on fire downtown",
            source="twitter_user",
            confidence=0.7
        ),
        Report(
            event_type="Fire",
            location="paris",
            timestamp="2025-09-14T12:15:00Z",
            description="Building on fire in city center",
            source="official_news_agency",
            confidence=0.9
        )
    ]
    # Debug: Check similarities
    sim_event = checker.similarity("fire", "Fire")
    sim_location = checker.similarity("Paris", "paris")
    sim_desc = checker.similarity("Building on fire downtown", "Building on fire in city center")
    print(f"Similarities - Event: {sim_event}, Location: {sim_location}, Description: {sim_desc}")
    
    clusters = checker._create_clusters(reports)
    assert len(clusters) == 1, f"Expected 1 cluster, got {len(clusters)}. Similarities: event={sim_event}, loc={sim_location}, desc={sim_desc}"

def checker_relaxed():
    return CheckerA({
        "event_type_similarity_threshold": 70,
        "location_similarity_threshold": 70,
        "description_similarity_threshold": 65
    })