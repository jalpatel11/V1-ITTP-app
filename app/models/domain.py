"""SQLAlchemy ORM Domain Models matching database/schema.sql.

Contains relational mappings for Corridors, Communities, Data Sources, Ingestion Runs,
Venues, Organizations, Categories, Events, Attractions, Businesses, Transportation Points,
and Data Quality Issues.
"""

import uuid
from datetime import datetime, date, time
from sqlalchemy import (
    Column, String, Text, Date, Time, DateTime, Integer, Numeric, ForeignKey, CheckConstraint, Table
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    """Generates a UUID4 string for primary keys.

    Returns:
        str: Standard UUID string.
    """
    return str(uuid.uuid4())


class Corridor(Base):
    """Represents a geographic tourism corridor (e.g. Bow River Corridor)."""
    __tablename__ = "corridors"

    corridor_id = Column(String(36), primary_key=True, default=generate_uuid)
    corridor_name = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    communities = relationship("Community", back_populates="corridor")


class Community(Base):
    """Represents a city, town, or municipal community."""
    __tablename__ = "communities"

    community_id = Column(String(36), primary_key=True, default=generate_uuid)
    community_name = Column(Text, nullable=False)
    municipality_type = Column(Text, nullable=True)
    province = Column(Text, default="Alberta")
    corridor_id = Column(String(36), ForeignKey("corridors.corridor_id"), nullable=True)
    notes = Column(Text, nullable=True)

    corridor = relationship("Corridor", back_populates="communities")
    venues = relationship("Venue", back_populates="community")
    events = relationship("Event", back_populates="community")


class DataSource(Base):
    """Represents a public data source (e.g. Tourism Red Deer, Town of Canmore)."""
    __tablename__ = "data_sources"

    source_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_name = Column(Text, nullable=False)
    source_owner = Column(Text, nullable=True)
    source_url = Column(Text, nullable=False)
    source_type = Column(Text, nullable=True)
    access_method = Column(Text, nullable=True)
    licence_notes = Column(Text, nullable=True)
    last_checked = Column(DateTime, nullable=True)

    events = relationship("Event", back_populates="source")
    ingestion_runs = relationship("IngestionRun", back_populates="source")


class IngestionRun(Base):
    """Tracks raw data collection and ETL pipeline execution runs."""
    __tablename__ = "ingestion_runs"

    ingestion_run_id = Column(String(36), primary_key=True, default=generate_uuid)
    source_id = Column(String(36), ForeignKey("data_sources.source_id"), nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow)
    collection_method = Column(Text, nullable=True)
    raw_file_name = Column(Text, nullable=True)
    record_count = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    source = relationship("DataSource", back_populates="ingestion_runs")
    events = relationship("Event", back_populates="ingestion_run")


class Venue(Base):
    """Represents physical venues, parks, or facilities hosting events."""
    __tablename__ = "venues"

    venue_id = Column(String(36), primary_key=True, default=generate_uuid)
    venue_name = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
    community_id = Column(String(36), ForeignKey("communities.community_id"), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    geocoding_status = Column(Text, default="pending")

    community = relationship("Community", back_populates="venues")
    events = relationship("Event", back_populates="venue")


class Organization(Base):
    """Represents event organizers or local business organizations."""
    __tablename__ = "organizations"

    organization_id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_name = Column(Text, nullable=False)
    organization_type = Column(Text, nullable=True)
    contact_email = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    website = Column(Text, nullable=True)
    community_id = Column(String(36), ForeignKey("communities.community_id"), nullable=True)

    events = relationship("Event", back_populates="organizer")


class Category(Base):
    """Represents standardized event categories."""
    __tablename__ = "categories"

    category_id = Column(String(36), primary_key=True, default=generate_uuid)
    category_name = Column(Text, nullable=False, unique=True)
    parent_category_id = Column(String(36), ForeignKey("categories.category_id"), nullable=True)
    description = Column(Text, nullable=True)


class Event(Base):
    """Core Event entity matching portal schema."""
    __tablename__ = "events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    external_event_id = Column(Text, nullable=True)
    event_name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    time_zone = Column(Text, default="America/Edmonton")
    venue_id = Column(String(36), ForeignKey("venues.venue_id"), nullable=True)
    community_id = Column(String(36), ForeignKey("communities.community_id"), nullable=True)
    source_id = Column(String(36), ForeignKey("data_sources.source_id"), nullable=False)
    organizer_id = Column(String(36), ForeignKey("organizations.organization_id"), nullable=True)
    source_link = Column(Text, nullable=False)
    last_checked = Column(Date, nullable=False, default=date.today)
    verification_status = Column(Text, nullable=False, default="unverified")
    quality_notes = Column(Text, nullable=True)
    ingestion_run_id = Column(String(36), ForeignKey("ingestion_runs.ingestion_run_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    venue = relationship("Venue", back_populates="events")
    community = relationship("Community", back_populates="events")
    source = relationship("DataSource", back_populates="events")
    organizer = relationship("Organization", back_populates="events")
    ingestion_run = relationship("IngestionRun", back_populates="events")
    quality_issues = relationship("DataQualityIssue", back_populates="event", cascade="all, delete-orphan")


class DataQualityIssue(Base):
    """Tracks data validation flags, missing fields, and duplicate risks."""
    __tablename__ = "data_quality_issues"

    issue_id = Column(String(36), primary_key=True, default=generate_uuid)
    related_table = Column(Text, nullable=False, default="events")
    related_record_id = Column(String(36), nullable=True)
    event_id = Column(String(36), ForeignKey("events.event_id", ondelete="CASCADE"), nullable=True)
    issue_type = Column(Text, nullable=False)
    issue_description = Column(Text, nullable=True)
    severity = Column(Text, default="medium")
    status = Column(Text, default="open")
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="quality_issues")
