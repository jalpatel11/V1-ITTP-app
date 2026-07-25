"""Communities API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.domain import Community, Corridor, Event
from app.schemas.domain import CommunitySchema
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/communities", tags=["Communities"])


@router.get("", response_model=List[CommunitySchema])
def list_communities(db: Session = Depends(get_db)) -> List[CommunitySchema]:
    """Returns list of active communities and municipal jurisdictions.

    Returns:
        List[CommunitySchema]: Active community records list.
    """
    try:
        log_info("list_communities", "Fetching communities list")
        communities_orm = db.query(Community).all()
        result: List[CommunitySchema] = []

        for comm in communities_orm:
            corr_name = comm.corridor.corridor_name if comm.corridor else None
            ev_count = db.query(func.count(Event.event_id)).filter(Event.community_id == comm.community_id).scalar() or 0

            result.append(CommunitySchema(
                community_id=comm.community_id,
                community_name=comm.community_name,
                municipality_type=comm.municipality_type,
                province=comm.province,
                corridor_name=corr_name,
                event_count=ev_count
            ))

        return result
    except Exception as e:
        log_error("list_communities", "Failed to retrieve communities list", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve communities"
        )
