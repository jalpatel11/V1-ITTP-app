"""Map GIS API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain import Event, Community, Venue, Corridor
from app.schemas.domain import MapEventSchema
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/map", tags=["Map"])


@router.get("/events", response_model=List[MapEventSchema])
def get_map_events(
    community: Optional[str] = Query(None, description="Filter map events by community"),
    corridor: Optional[str] = Query(None, description="Filter map events by corridor"),
    category: Optional[str] = Query(None, description="Filter map events by category"),
    db: Session = Depends(get_db)
) -> List[MapEventSchema]:
    """Returns event points formatted for interactive map marker display.

    Returns:
        List[MapEventSchema]: Map marker event point list.
    """
    try:
        log_info("get_map_events", "Fetching map event point markers")
        query = db.query(Event).join(Event.community)

        if community:
            query = query.filter(Community.community_name.ilike(f"%{community}%"))
        if corridor:
            query = query.join(Community.corridor).filter(Corridor.corridor_name.ilike(f"%{corridor}%"))
        if category:
            query = query.filter(Event.category.ilike(f"%{category}%"))

        events_orm = query.all()
        result: List[MapEventSchema] = []

        for ev in events_orm:
            comm_name = ev.community.community_name if ev.community else "Unknown"
            v_name = ev.venue.venue_name if ev.venue else None
            v_addr = ev.venue.address if ev.venue else None
            lat = float(ev.venue.latitude) if ev.venue and ev.venue.latitude is not None else None
            lng = float(ev.venue.longitude) if ev.venue and ev.venue.longitude is not None else None

            result.append(MapEventSchema(
                event_id=ev.event_id,
                event_name=ev.event_name,
                category=ev.category or "Community gathering",
                start_date=ev.start_date,
                latitude=lat,
                longitude=lng,
                venue_name=v_name,
                address=v_addr,
                municipality=comm_name,
                verification_status=ev.verification_status
            ))

        return result
    except Exception as e:
        log_error("get_map_events", "Failed to retrieve map events", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve map event markers"
        )
