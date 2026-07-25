"""Events API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
Rule 1.9: Comprehensive try-catch and logging context.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.domain import Event, Community, Venue, DataSource, Corridor
from app.schemas.domain import EventSchema, EventListResponse
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/events", tags=["Events"])


def format_event_schema(ev: Event) -> EventSchema:
    """Formats SQLAlchemy Event ORM instance into clean Pydantic EventSchema payload.

    Args:
        ev: SQLAlchemy Event ORM instance.

    Returns:
        EventSchema: Standardized Pydantic Event model.
    """
    comm_name = ev.community.community_name if ev.community else "Unknown"
    corr_name = ev.community.corridor.corridor_name if ev.community and ev.community.corridor else None
    v_name = ev.venue.venue_name if ev.venue else None
    v_addr = ev.venue.address if ev.venue else None
    lat = float(ev.venue.latitude) if ev.venue and ev.venue.latitude is not None else None
    lng = float(ev.venue.longitude) if ev.venue and ev.venue.longitude is not None else None
    src_name = ev.source.source_name if ev.source else "Public Source"

    return EventSchema(
        event_id=ev.event_id,
        external_event_id=ev.external_event_id,
        event_name=ev.event_name,
        description=ev.description,
        category=ev.category or "Community gathering",
        start_date=ev.start_date,
        end_date=ev.end_date,
        start_time=ev.start_time,
        end_time=ev.end_time,
        time_zone=ev.time_zone or "America/Edmonton",
        venue_name=v_name,
        address=v_addr,
        municipality=comm_name,
        corridor=corr_name,
        latitude=lat,
        longitude=lng,
        source_name=src_name,
        source_link=ev.source_link,
        last_checked=ev.last_checked or date.today(),
        verification_status=ev.verification_status,
        quality_notes=ev.quality_notes
    )


@router.get("", response_model=EventListResponse)
def list_events(
    community: Optional[str] = Query(None, description="Filter by municipality or community name"),
    corridor: Optional[str] = Query(None, description="Filter by corridor name"),
    category: Optional[str] = Query(None, description="Filter by event category"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    start_date: Optional[date] = Query(None, description="Filter events starting on or after date"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> EventListResponse:
    """Fetches paginated list of events matching query filter criteria.

    Returns:
        EventListResponse: Paginated events payload.
    """
    try:
        log_info("list_events", "Querying events", {
            "community": community, "category": category, "limit": limit, "offset": offset
        })
        query = db.query(Event)

        if community:
            query = query.join(Event.community).filter(Community.community_name.ilike(f"%{community}%"))
        if corridor:
            query = query.join(Event.community).join(Community.corridor).filter(Corridor.corridor_name.ilike(f"%{corridor}%"))
        if category:
            query = query.filter(Event.category.ilike(f"%{category}%"))
        if verification_status:
            query = query.filter(Event.verification_status == verification_status)
        if start_date:
            query = query.filter(Event.start_date >= start_date)

        total = query.count()
        events_orm = query.order_by(Event.start_date.asc()).offset(offset).limit(limit).all()

        formatted_events = [format_event_schema(e) for e in events_orm]

        return EventListResponse(
            total=total,
            limit=limit,
            offset=offset,
            events=formatted_events
        )
    except Exception as e:
        log_error("list_events", "Failed to retrieve events list", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events"
        )


@router.get("/search", response_model=EventListResponse)
def search_events(
    q: str = Query(..., min_length=1, description="Search keyword in title, description, or municipality"),
    community: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> EventListResponse:
    """Searches event listings by keyword across title, description, and municipality.

    Returns:
        EventListResponse: Search matching events list.
    """
    try:
        log_info("search_events", f"Searching events for query '{q}'")
        search_filter = or_(
            Event.event_name.ilike(f"%{q}%"),
            Event.description.ilike(f"%{q}%"),
            Event.category.ilike(f"%{q}%")
        )
        query = db.query(Event).filter(search_filter)

        if community:
            query = query.join(Event.community).filter(Community.community_name.ilike(f"%{community}%"))
        if category:
            query = query.filter(Event.category.ilike(f"%{category}%"))

        total = query.count()
        events_orm = query.order_by(Event.start_date.asc()).offset(offset).limit(limit).all()

        return EventListResponse(
            total=total,
            limit=limit,
            offset=offset,
            events=[format_event_schema(e) for e in events_orm]
        )
    except Exception as e:
        log_error("search_events", f"Failed search for query '{q}'", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search query failed"
        )


@router.get("/{event_id}", response_model=EventSchema)
def get_event_detail(event_id: str, db: Session = Depends(get_db)) -> EventSchema:
    """Retrieves full details for a single event record by ID or external ID.

    Args:
        event_id: Primary key UUID or external_event_id string.

    Returns:
        EventSchema: Complete event detail payload.
    """
    try:
        log_info("get_event_detail", f"Fetching event details for '{event_id}'")
        ev = db.query(Event).filter(or_(Event.event_id == event_id, Event.external_event_id == event_id)).first()
        if not ev:
            log_error("get_event_detail", f"Event not found for id '{event_id}'")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID '{event_id}' not found."
            )
        return format_event_schema(ev)
    except HTTPException:
        raise
    except Exception as e:
        log_error("get_event_detail", f"Error getting event detail for '{event_id}'", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event detail"
        )
