# tests/test_detecter.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from src.detecter.detecter import DetecterA, GeoCoder

@pytest.fixture
def mock_db_session():
    session = MagicMock(spec=AsyncSession)
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    return session

@pytest.fixture
def detecter(mock_db_session):
    return DetecterA(mock_db_session)

def test_haversine_distance():
    # NYC to LA ~3940km
    nyc = (40.7128, -74.0060)
    la = (34.0522, -118.2437)
    dist = haversine_distance(nyc, la)
    assert 3900 < dist < 4000

@patch('src.detecter.detecter.requests.get')
def test_geocode_success(mock_get, detecter):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"lat": "40.7128", "lon": "-74.0060"}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    coords = detecter.geocoder.geocode("New York City")
    assert coords == (40.7128, -74.0060)

@patch('src.detecter.detecter.requests.get')
def test_geocode_failure(mock_get, detecter):
    mock_get.side_effect = Exception("API down")
    coords = detecter.geocoder.geocode("Invalid Location")
    assert coords is None

@pytest.mark.asyncio
async def test_cluster_points(detecter):
    points = [
        {"latitude": 40.7128, "longitude": -74.0060, "confidence": 1.0, "type": "human", "payload": MagicMock()},
        {"latitude": 40.7130, "longitude": -74.0062, "confidence": 1.0, "type": "disaster", "payload": MagicMock()},
    ]
    clusters = detecter.cluster_points(points)
    assert len(clusters) == 1
    assert len(clusters[0]) == 2