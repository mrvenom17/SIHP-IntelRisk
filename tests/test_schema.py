# tests/test_schema.py
import json
import pytest
from jsonschema import validate, ValidationError

# Load schema
with open('src/schema/schema.json') as f:
    schema = json.load(f)

def test_valid_composite_hotspot():
    valid_hotspot = {
        "latitude": -6.2088,
        "longitude": 106.8456,
        "aggregated_emotions": {"fear": 0.85},
        "average_panic_level": 0.78,
        "event_types": ["flood"],
        "severity_level": "high",
        "risk_level": "high",
        "contributing_reports": 12
    }
    validate(instance=valid_hotspot, schema=schema['definitions']['CompositeHotspot'])

def test_invalid_latitude():
    invalid_hotspot = {
        "latitude": 95.0,  # Invalid
        "longitude": 106.8456,
        "aggregated_emotions": {"fear": 0.85},
        "average_panic_level": 0.78,
        "event_types": ["flood"],
        "severity_level": "high",
        "risk_level": "high",
        "contributing_reports": 12
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_hotspot, schema=schema['definitions']['CompositeHotspot'])

def test_valid_map_json():
    valid_map = {
        "hotspots": [
            {
                "latitude": -6.2088,
                "longitude": 106.8456,
                "aggregated_emotions": {"fear": 0.85},
                "average_panic_level": 0.78,
                "event_types": ["flood"],
                "severity_level": "high",
                "risk_level": "high",
                "contributing_reports": 12
            }
        ]
    }
    validate(instance=valid_map, schema=schema['definitions']['MapJSON'])