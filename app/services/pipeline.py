"""Data Cleaning, Validation, and ETL Ingestion Pipeline.

Rule 1.1: Clear Comments on All Business Functions.
Rule 1.6: Single Responsibility Principle.
Rule 1.9: Error Logging with context.
"""

import os
import csv
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.domain import (
    Corridor, Community, DataSource, IngestionRun, Venue, Category, Event, DataQualityIssue
)
from app.utils.logger import log_error, log_info

# Municipal centroids mapping for initial geocoding fallback demo
MUNICIPAL_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Red Deer": (52.2681, -113.8112),
    "Springbrook / Red Deer area": (52.1814, -113.8647),
    "Elnora / Red Deer area": (51.9961, -113.2081),
    "Canmore": (51.0890, -115.3598),
    "Drumheller": (51.4644, -112.7108),
    "Drumheller area": (51.4644, -112.7108),
    "Trochu / Drumheller area": (51.8267, -113.2208)
}

# Corridor assignment mapping by municipality
MUNICIPAL_CORRIDOR: Dict[str, str] = {
    "Red Deer": "Red Deer River Corridor",
    "Springbrook / Red Deer area": "Red Deer River Corridor",
    "Elnora / Red Deer area": "Red Deer River Corridor",
    "Canmore": "Bow River Corridor",
    "Drumheller": "Red Deer River Corridor",
    "Drumheller area": "Red Deer River Corridor",
    "Trochu / Drumheller area": "Red Deer River Corridor"
}

APPROVED_CATEGORIES = [
    "Outdoor recreation", "Parks and trails", "Food and drink", "Music",
    "Arts and culture", "Family activities", "Sports", "History and heritage",
    "Indigenous tourism and culture", "Festival or market", "Museum or education",
    "Local business event", "Seasonal activity", "Community gathering", "Transportation-related event"
]


def clean_text_field(value: Optional[str]) -> str:
    """Cleans whitespace, linebreaks, and special characters from text string.

    Args:
        value: Raw text string or None.

    Returns:
        str: Cleaned and normalized text.
    """
    if not value:
        return ""
    cleaned = value.strip().replace("\n", " ").replace("\r", "")
    # Fix broken city trailing digits e.g. "Red Deer1" -> "Red Deer"
    if cleaned == "Red Deer1":
        cleaned = "Red Deer"
    return cleaned


def infer_category(event_title: str, notes: str) -> str:
    """Infers standard event category based on title and raw notes keywords.

    Args:
        event_title: Event title string.
        notes: Raw notes string.

    Returns:
        str: Approved category name.
    """
    text = (event_title + " " + notes).lower()
    if any(k in text for k in ["airshow", "market", "festival", "parade", "feast"]):
        return "Festival or market"
    if any(k in text for k in ["disco", "music", "dance", "band", "concert"]):
        return "Music"
    if any(k in text for k in ["bat walks", "outdoor", "park", "trail", "farm", "recreation"]):
        return "Outdoor recreation"
    if any(k in text for k in ["talk", "tour", "museum", "art", "gallery"]):
        return "Museum or education"
    if any(k in text for k in ["toys", "babies", "family", "kids"]):
        return "Family activities"
    if any(k in text for k in ["lunch", "happy hour", "high tea", "food", "grill"]):
        return "Food and drink"
    return "Community gathering"


def parse_date_string(date_str: str) -> Optional[date]:
    """Parses date string into date object.

    Args:
        date_str: Raw date string (e.g., '2026-07-24').

    Returns:
        Optional[date]: Parsed date or None.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def run_etl_pipeline(
    raw_csv_path: str,
    processed_csv_path: str,
    validation_log_path: str,
    db: Session
) -> Dict[str, Any]:
    """Runs full ETL pipeline: loads raw CSV, cleans text/dates, checks validation rules,
    exports processed CSV & log CSV, and loads records into database tables.

    Args:
        raw_csv_path: Absolute path to raw CSV file.
        processed_csv_path: Absolute path to processed output CSV.
        validation_log_path: Absolute path to validation log output CSV.
        db: Active SQLAlchemy database session.

    Returns:
        Dict[str, Any]: Summary dictionary of records processed, cleaned, and issues logged.
    """
    log_info("run_etl_pipeline", "Starting event data ingestion pipeline", {"raw_csv": raw_csv_path})

    if not os.path.exists(raw_csv_path):
        err_msg = f"Raw CSV file not found at {raw_csv_path}"
        log_error("run_etl_pipeline", err_msg)
        raise FileNotFoundError(err_msg)

    # Prepare directories
    os.makedirs(os.path.dirname(processed_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(validation_log_path), exist_ok=True)

    cleaned_records: List[Dict[str, Any]] = []
    validation_logs: List[Dict[str, Any]] = []
    seen_events: Dict[str, str] = {}  # Deduplication key -> raw_id

    # Create default data source and corridor records in DB
    corridor_map = {}
    for name in ["Red Deer River Corridor", "Bow River Corridor"]:
        c = db.query(Corridor).filter_by(corridor_name=name).first()
        if not c:
            c = Corridor(corridor_name=name, description=f"Tourism region for {name}")
            db.add(c)
            db.flush()
        corridor_map[name] = c.corridor_id

    source_map = {}
    
    with open(raw_csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = clean_text_field(row.get("raw_id"))
            source_name = clean_text_field(row.get("source_name"))
            raw_title = clean_text_field(row.get("raw_event_title"))
            raw_date = clean_text_field(row.get("raw_date"))
            raw_start_time = clean_text_field(row.get("raw_start_time"))
            raw_end_date = clean_text_field(row.get("raw_end_date"))
            raw_end_time = clean_text_field(row.get("raw_end_time"))
            raw_venue = clean_text_field(row.get("raw_venue"))
            raw_address = clean_text_field(row.get("raw_address"))
            raw_muni = clean_text_field(row.get("raw_municipality"))
            source_link = clean_text_field(row.get("source_link"))
            raw_notes = clean_text_field(row.get("raw_notes"))

            # 1. Cleaning & Standardizing
            parsed_start_date = parse_date_string(raw_date)
            parsed_end_date = parse_date_string(raw_end_date) if raw_end_date else parsed_start_date
            category = infer_category(raw_title, raw_notes)
            corridor_name = MUNICIPAL_CORRIDOR.get(raw_muni, "Red Deer River Corridor")

            # Fallback coordinates check
            coords = MUNICIPAL_COORDINATES.get(raw_muni, (None, None))
            lat, lng = coords if coords != (None, None) else (None, None)
            geocoding_status = "verified" if lat else "geocoding_pending"
            verification_status = "needs_review" if "review" in raw_notes.lower() or not raw_venue or raw_venue.startswith("Not listed") else "verified"

            # 2. Validation Checks & Issues Logging
            # Issue check 1: Missing Title
            if not raw_title:
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "missing_title",
                    "field_name": "raw_event_title",
                    "issue_description": "Event record is missing a title.",
                    "severity": "high",
                    "recommended_action": "Manually inspect source link for title."
                })

            # Issue check 2: Missing Date
            if not parsed_start_date:
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "missing_start_date",
                    "field_name": "raw_date",
                    "issue_description": "Event start date is missing or malformed.",
                    "severity": "high",
                    "recommended_action": "Parse date from raw event page body."
                })

            # Issue check 3: Missing Location / Address details
            if not raw_venue or raw_venue.startswith("Not listed") or "Not listed" in raw_address:
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "missing_location_details",
                    "field_name": "raw_venue",
                    "issue_description": "Venue is unlisted in summary calendar view.",
                    "severity": "medium",
                    "recommended_action": "Scrape detailed event page to extract venue name and street address."
                })

            # Issue check 4: Geocoding Pending / Missing Coordinates
            if not lat or not lng:
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "missing_coordinates",
                    "field_name": "latitude/longitude",
                    "issue_description": "Precise street geocoding coordinates are missing.",
                    "severity": "low",
                    "recommended_action": "Run address through geocoding API."
                })

            # Issue check 5: Historical / Expired Events
            reference_date = date(2026, 1, 1)
            if parsed_start_date and parsed_start_date < reference_date:
                verification_status = "expired"
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "expired_event",
                    "field_name": "start_date",
                    "issue_description": f"Event occurred in {parsed_start_date.year} (prior to pilot baseline).",
                    "severity": "low",
                    "recommended_action": "Archive historical record or exclude from active view."
                })

            # Issue check 6: Duplicate Risk Detection
            dedup_key = f"{raw_title.lower()}|{raw_date}|{raw_venue.lower()}"
            if dedup_key in seen_events:
                validation_logs.append({
                    "event_id": raw_id,
                    "issue_type": "possible_duplicate_risk",
                    "field_name": "raw_event_title",
                    "issue_description": f"Same title, date, and venue match previous event {seen_events[dedup_key]}.",
                    "severity": "medium",
                    "recommended_action": "Verify if recurring instance or accidental duplicate."
                })
            else:
                seen_events[dedup_key] = raw_id

            cleaned_record = {
                "event_id": raw_id,
                "source_name": source_name,
                "event_name": raw_title,
                "description": f"Event in {raw_muni}. Source notes: {raw_notes}",
                "category": category,
                "start_date": str(parsed_start_date) if parsed_start_date else "",
                "end_date": str(parsed_end_date) if parsed_end_date else "",
                "start_time": raw_start_time,
                "end_time": raw_end_time,
                "time_zone": "America/Edmonton",
                "venue_name": raw_venue,
                "address": raw_address,
                "municipality": raw_muni,
                "corridor": corridor_name,
                "latitude": lat,
                "longitude": lng,
                "source_link": source_link,
                "verification_status": verification_status,
                "last_checked": str(date.today())
            }
            cleaned_records.append(cleaned_record)

            # 3. Database Insertion Logic
            # DataSource lookup/insert
            if source_name not in source_map:
                src = db.query(DataSource).filter_by(source_name=source_name).first()
                if not src:
                    src = DataSource(
                        source_name=source_name,
                        source_url=source_link,
                        source_type="public_web",
                        last_checked=datetime.utcnow()
                    )
                    db.add(src)
                    db.flush()
                source_map[source_name] = src.source_id

            # Community lookup/insert
            comm = db.query(Community).filter_by(community_name=raw_muni).first()
            if not comm:
                comm = Community(
                    community_name=raw_muni,
                    municipality_type="Municipality",
                    corridor_id=corridor_map[corridor_name]
                )
                db.add(comm)
                db.flush()

            # Venue lookup/insert
            v = None
            if raw_venue:
                v = db.query(Venue).filter_by(venue_name=raw_venue, community_id=comm.community_id).first()
                if not v:
                    v = Venue(
                        venue_name=raw_venue,
                        address=raw_address,
                        community_id=comm.community_id,
                        latitude=lat,
                        longitude=lng,
                        geocoding_status=geocoding_status
                    )
                    db.add(v)
                    db.flush()

            # Event lookup/upsert
            ev = db.query(Event).filter_by(external_event_id=raw_id).first()
            if not ev:
                ev = Event(
                    external_event_id=raw_id,
                    event_name=raw_title,
                    description=f"Event in {raw_muni}. Source notes: {raw_notes}",
                    category=category,
                    start_date=parsed_start_date or date.today(),
                    end_date=parsed_end_date,
                    start_time=datetime.strptime(raw_start_time, "%H:%M").time() if raw_start_time and len(raw_start_time) == 5 else None,
                    end_time=datetime.strptime(raw_end_time, "%H:%M").time() if raw_end_time and len(raw_end_time) == 5 else None,
                    time_zone="America/Edmonton",
                    venue_id=v.venue_id if v else None,
                    community_id=comm.community_id,
                    source_id=source_map[source_name],
                    source_link=source_link,
                    last_checked=date.today(),
                    verification_status=verification_status,
                    quality_notes=raw_notes
                )
                db.add(ev)
                db.flush()

            # Add quality issues to DB
            for issue in [log for log in validation_logs if log["event_id"] == raw_id]:
                q_issue = DataQualityIssue(
                    event_id=ev.event_id,
                    related_table="events",
                    issue_type=issue["issue_type"],
                    issue_description=issue["issue_description"],
                    severity=issue["severity"],
                    status="open"
                )
                db.add(q_issue)

    db.commit()

    # 4. Export Processed CSV & Validation Log CSV
    if cleaned_records:
        fieldnames = list(cleaned_records[0].keys())
        with open(processed_csv_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cleaned_records)

    if validation_logs:
        log_fieldnames = ["event_id", "issue_type", "field_name", "issue_description", "severity", "recommended_action"]
        with open(validation_log_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=log_fieldnames)
            writer.writeheader()
            writer.writerows(validation_logs)

    log_info("run_etl_pipeline", "ETL ingestion completed successfully", {
        "processed_count": len(cleaned_records),
        "validation_issues_count": len(validation_logs)
    })

    return {
        "processed_count": len(cleaned_records),
        "validation_issues_count": len(validation_logs),
        "processed_csv": processed_csv_path,
        "validation_log_csv": validation_log_path
    }
