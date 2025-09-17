# tests/test_models.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models import RawPost, Report, HumanHotspot, DisasterHotspot, CompositeHotspot, ProcessStatus, AggregateStatus

@pytest.mark.asyncio
async def test_raw_post_creation(db_session: AsyncSession):
    raw = RawPost(content={"text": "Flood in Jakarta"}, hash="abc123", status=ProcessStatus.pending)
    db_session.add(raw)
    await db_session.commit()
    assert raw.id is not None

@pytest.mark.asyncio
async def test_report_relationship(db_session: AsyncSession):
    raw = RawPost(content={"text": "Fire in LA"}, hash="def456", status=ProcessStatus.pending)
    db_session.add(raw)
    await db_session.commit()

    report = Report(
        raw_post_id=raw.id,
        event_type="fire",
        location="LA",
        description="Wildfire spreading",
        source="news",
        status=ProcessStatus.pending
    )
    db_session.add(report)
    await db_session.commit()

    assert report.raw_post.id == raw.id
    assert len(raw.reports) == 1

@pytest.mark.asyncio
async def test_composite_hotspot_creation(db_session: AsyncSession):
    ch = CompositeHotspot(
        latitude=40.7128,
        longitude=-74.0060,
        severity_level="high",
        risk_level="critical",
        contributing_reports_count=5
    )
    db_session.add(ch)
    await db_session.commit()
    assert ch.id is not None
    assert ch.severity_level == "high"