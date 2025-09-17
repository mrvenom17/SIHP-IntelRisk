# src/core/models.py
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, ForeignKey, Float, Enum, Table, Index, text
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from enum import Enum as PyEnum

# Use async-compatible base
Base = declarative_base()

class ProcessStatus(PyEnum):
    pending = "pending"
    processing = "processing"
    processed = "processed"
    error = "error"

class AggregateStatus(PyEnum):
    pending = "pending"
    aggregated = "aggregated"
    error = "error"

# Association table
compositehotspot_report = Table(
    "compositehotspot_report",
    Base.metadata,
    Column("compositehotspot_id", Integer, ForeignKey("composite_hotspots.id", ondelete="CASCADE"), primary_key=True),
    Column("report_id", Integer, ForeignKey("reports.id", ondelete="CASCADE"), primary_key=True),
    Index('idx_compositehotspot_report_composite', 'compositehotspot_id'),
    Index('idx_compositehotspot_report_report', 'report_id'),
)

class RawPost(Base):
    __tablename__ = "raw_posts"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(JSON, nullable=False)
    hash = Column(String(64), unique=True, nullable=False)
    prev_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(ProcessStatus), nullable=False, default=ProcessStatus.pending)

    reports = relationship(
        "Report",
        back_populates="raw_post",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True
    )

    # Indexes for agent queries
    __table_args__ = (
        Index('idx_raw_posts_status', 'status'),
        Index('idx_raw_posts_timestamp', 'timestamp'),
    )

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    raw_post_id = Column(Integer, ForeignKey("raw_posts.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=True, index=True)
    location = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    description = Column(String, nullable=True)
    source = Column(String, nullable=True, index=True)
    media_urls = Column(JSON, default=list)
    reporter = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    veracity_flag = Column(String, nullable=True, index=True)
    status = Column(Enum(ProcessStatus), nullable=False, default=ProcessStatus.pending)

    raw_post = relationship("RawPost", back_populates="reports")

    human_hotspot = relationship(
        "HumanHotspot",
        uselist=False,
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True
    )

    disaster_hotspot = relationship(
        "DisasterHotspot",
        uselist=False,
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True
    )

    composite_hotspots = relationship(
        "CompositeHotspot",
        secondary=compositehotspot_report,
        back_populates="reports"
    )

    __table_args__ = (
        Index('idx_reports_status_veracity', 'status', 'veracity_flag'),
        Index('idx_reports_location', 'location'),
    )

class HumanHotspot(Base):
    __tablename__ = "human_hotspots"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    location = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    emotions = Column(JSON, nullable=True)
    panic_level = Column(String, nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    status = Column(Enum(AggregateStatus), nullable=False, default=AggregateStatus.pending)

    report = relationship("Report", back_populates="human_hotspot")

    __table_args__ = (
        Index('idx_human_hotspots_status', 'status'),
        Index('idx_human_hotspots_location', 'location'),
    )

class DisasterHotspot(Base):
    __tablename__ = "disaster_hotspots"
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, unique=True)
    location = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    event_type = Column(String, nullable=True, index=True)
    severity = Column(String, nullable=False, index=True)
    risk_level = Column(String, nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    status = Column(Enum(AggregateStatus), nullable=False, default=AggregateStatus.pending)

    report = relationship("Report", back_populates="disaster_hotspot")

    __table_args__ = (
        Index('idx_disaster_hotspots_status', 'status'),
        Index('idx_disaster_hotspots_location', 'location'),
        Index('idx_disaster_hotspots_severity', 'severity'),
    )

class CompositeHotspot(Base):
    __tablename__ = "composite_hotspots"
    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    aggregated_emotions = Column(JSON, nullable=True)
    average_panic_level = Column(Float, nullable=True)
    event_types = Column(JSON, nullable=True)
    severity_level = Column(String, nullable=False, default="low")
    risk_level = Column(String, nullable=False, default="unknown")
    contributing_reports_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    reports = relationship(
        "Report",
        secondary=compositehotspot_report,
        back_populates="composite_hotspots",
        passive_deletes=True
    )

    __table_args__ = (
        Index('idx_composite_hotspots_created_at', 'created_at'),
        Index('idx_composite_hotspots_location', 'latitude', 'longitude'),
        Index('idx_composite_hotspots_severity', 'severity_level'),
    )