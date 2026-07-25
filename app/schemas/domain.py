"""Pydantic Request & Response Validation Schemas matching portal API specification.

Rule 1.11: Avoid any, use explicit typed Pydantic models.
"""

from typing import Optional, List
from datetime import date, time, datetime
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Health check endpoint response schema."""
    status: str = "ok"
    service: str = "tourism-portal-api"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VenueSchema(BaseModel):
    """Venue details response schema."""
    venue_id: str
    venue_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geocoding_status: str = "pending"

    model_config = ConfigDict(from_attributes=True)


class CommunitySchema(BaseModel):
    """Community response schema."""
    community_id: str
    community_name: str
    municipality_type: Optional[str] = None
    province: str = "Alberta"
    corridor_name: Optional[str] = None
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CategorySchema(BaseModel):
    """Category response schema."""
    category_id: str
    category_name: str
    description: Optional[str] = None
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class EventSchema(BaseModel):
    """Standard Event response schema matching 03_EVENT_SCHEMA.md."""
    event_id: str
    external_event_id: Optional[str] = None
    event_name: str
    description: Optional[str] = None
    category: str
    start_date: date
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    time_zone: str = "America/Edmonton"
    venue_name: Optional[str] = None
    address: Optional[str] = None
    municipality: str
    corridor: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_name: str
    source_link: str
    last_checked: date
    verification_status: str = "unverified"
    quality_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """Paginated list of events response."""
    total: int
    limit: int
    offset: int
    events: List[EventSchema]


class MapEventSchema(BaseModel):
    """Simplified Event payload for map marker rendering matching 06_API_SPEC.md."""
    event_id: str
    event_name: str
    category: str
    start_date: date
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    venue_name: Optional[str] = None
    address: Optional[str] = None
    municipality: str
    verification_status: str


class CategoryCount(BaseModel):
    """Count of events per category."""
    category: str
    count: int


class CommunityCount(BaseModel):
    """Count of events per community."""
    community: str
    count: int


class DashboardSummarySchema(BaseModel):
    """Summary metrics response for dashboard preview matching 06_API_SPEC.md & 09_DASHBOARD_METRICS.md."""
    total_events: int
    communities_count: int
    events_with_missing_coordinates: int
    needs_review_count: int
    expired_count: int
    categories: List[CategoryCount]
    communities: List[CommunityCount]
    quality_issue_count: int


class DataQualityIssueSchema(BaseModel):
    """Data quality issue response schema."""
    issue_id: str
    event_id: Optional[str] = None
    related_table: str
    issue_type: str
    issue_description: Optional[str] = None
    severity: str
    status: str
    detected_at: datetime

    model_config = ConfigDict(from_attributes=True)
