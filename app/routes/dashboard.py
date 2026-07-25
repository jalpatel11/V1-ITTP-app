"""Municipality Dashboard Preview API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.domain import Event, Community, Venue, DataQualityIssue
from app.schemas.domain import DashboardSummarySchema, CategoryCount, CommunityCount
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummarySchema)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummarySchema:
    """Returns aggregated summary metrics for municipality and tourism dashboards.

    Returns:
        DashboardSummarySchema: Summary indicators payload.
    """
    try:
        log_info("get_dashboard_summary", "Generating dashboard summary metrics")

        total_events = db.query(func.count(Event.event_id)).scalar() or 0
        communities_count = db.query(func.count(Community.community_id)).scalar() or 0

        # Missing coordinates count (venues with null lat/lng)
        missing_coords_count = (
            db.query(func.count(Event.event_id))
            .outerjoin(Event.venue)
            .filter((Venue.latitude.is_(None)) | (Venue.longitude.is_(None)))
            .scalar() or 0
        )

        needs_review_count = (
            db.query(func.count(Event.event_id))
            .filter(Event.verification_status == "needs_review")
            .scalar() or 0
        )

        expired_count = (
            db.query(func.count(Event.event_id))
            .filter(Event.verification_status == "expired")
            .scalar() or 0
        )

        quality_issue_count = db.query(func.count(DataQualityIssue.issue_id)).scalar() or 0

        # Category distribution
        cat_rows = (
            db.query(Event.category, func.count(Event.event_id))
            .group_by(Event.category)
            .all()
        )
        categories = [
            CategoryCount(category=row[0] or "Uncategorized", count=row[1])
            for row in cat_rows
        ]

        # Community distribution
        comm_rows = (
            db.query(Community.community_name, func.count(Event.event_id))
            .join(Event.community)
            .group_by(Community.community_name)
            .all()
        )
        communities = [
            CommunityCount(community=row[0], count=row[1])
            for row in comm_rows
        ]

        return DashboardSummarySchema(
            total_events=total_events,
            communities_count=communities_count,
            events_with_missing_coordinates=missing_coords_count,
            needs_review_count=needs_review_count,
            expired_count=expired_count,
            categories=categories,
            communities=communities,
            quality_issue_count=quality_issue_count
        )
    except Exception as e:
        log_error("get_dashboard_summary", "Failed to compute dashboard metrics", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute dashboard metrics"
        )
