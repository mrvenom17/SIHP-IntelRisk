# src/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, REGISTRY

def create_metric(metric_class, name, doc, labels=None):
    try:
        return metric_class(name, doc, labels or [])
    except ValueError:
        return REGISTRY._names_to_collectors.get(name) or metric_class(name + "_v2", doc, labels or [])

# Define all metrics here — imported once globally