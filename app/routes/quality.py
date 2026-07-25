"""Data Quality Issues API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain import DataQualityIssue
from app.schemas.domain import DataQualityIssueSchema
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/data-quality", tags=["Data Quality"])


@router.get("/issues", response_model=List[DataQualityIssueSchema])
def list_quality_issues(
    severity: Optional[str] = Query(None, description="Filter by severity level: high, medium, low"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type string"),
    db: Session = Depends(get_db)
) -> List[DataQualityIssueSchema]:
    """Returns detected data quality validation flags and records.

    Returns:
        List[DataQualityIssueSchema]: List of quality issues.
    """
    try:
        log_info("list_quality_issues", "Fetching data quality issues")
        query = db.query(DataQualityIssue)

        if severity:
            query = query.filter(DataQualityIssue.severity == severity)
        if issue_type:
            query = query.filter(DataQualityIssue.issue_type == issue_type)

        issues_orm = query.order_by(DataQualityIssue.detected_at.desc()).all()
        return [DataQualityIssueSchema.model_validate(iss) for iss in issues_orm]
    except Exception as e:
        log_error("list_quality_issues", "Failed to retrieve quality issues", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve data quality issues"
        )
