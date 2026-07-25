"""Categories API Route Controller.

Rule 1.2: All backend API routes use /api/* prefix.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.domain import Event
from app.schemas.domain import CategorySchema
from app.services.pipeline import APPROVED_CATEGORIES
from app.utils.logger import log_error, log_info

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[CategorySchema])
def list_categories(db: Session = Depends(get_db)) -> List[CategorySchema]:
    """Returns supported event categories and current record counts.

    Returns:
        List[CategorySchema]: Supported category list.
    """
    try:
        log_info("list_categories", "Fetching categories list")
        result: List[CategorySchema] = []

        for idx, cat_name in enumerate(APPROVED_CATEGORIES, start=1):
            count = db.query(func.count(Event.event_id)).filter(Event.category == cat_name).scalar() or 0
            result.append(CategorySchema(
                category_id=f"CAT-{idx:03d}",
                category_name=cat_name,
                description=f"Standard category for {cat_name.lower()}",
                event_count=count
            ))

        return result
    except Exception as e:
        log_error("list_categories", "Failed to retrieve categories list", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )
