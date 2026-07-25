"""Backend Automated Pytest Test Suite.

Rule 1.10: Unit Testing for all backend endpoints and ETL logic.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import init_db, SessionLocal
from app.services.pipeline import run_etl_pipeline

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Module setup fixture initializing DB and running sample data ETL."""
    init_db()
    db = SessionLocal()
    raw_csv = "data/raw/Week3_Task_3_raw_event_sample.csv"
    proc_csv = "data/processed/Week3_Task_3_standardised_event_sample.csv"
    val_log = "data/validation_logs/Week3_Task_3_data_quality_validation_log.csv"
    run_etl_pipeline(raw_csv, proc_csv, val_log, db)
    db.close()


def test_health_endpoint():
    """Tests GET /health response status and schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "tourism-portal-api"
    assert "version" in data


def test_list_events():
    """Tests GET /api/events endpoint."""
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "events" in data
    assert data["total"] > 0
    assert len(data["events"]) > 0


def test_event_search():
    """Tests GET /api/events/search endpoint."""
    response = client.get("/api/events/search?q=Airshow")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "Airshow" in data["events"][0]["event_name"]


def test_get_event_detail():
    """Tests GET /api/events/{event_id} detail route."""
    response = client.get("/api/events/RD-001")
    assert response.status_code == 200
    data = response.json()
    assert data["external_event_id"] == "RD-001"
    assert data["event_name"] == "Red Deer Regional Airshow"


def test_map_events():
    """Tests GET /api/map/events route for map coordinates payload."""
    response = client.get("/api/map/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "latitude" in data[0]
    assert "longitude" in data[0]


def test_dashboard_summary():
    """Tests GET /api/dashboard/summary endpoint metrics."""
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] > 0
    assert data["communities_count"] > 0
    assert "categories" in data
    assert "communities" in data


def test_communities():
    """Tests GET /api/communities route."""
    response = client.get("/api/communities")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "community_name" in data[0]


def test_categories():
    """Tests GET /api/categories route."""
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "category_name" in data[0]


def test_data_quality_issues():
    """Tests GET /api/data-quality/issues route."""
    response = client.get("/api/data-quality/issues")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "issue_type" in data[0]
