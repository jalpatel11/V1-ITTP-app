"""Standalone CLI script to execute raw CSV event data ingestion & validation pipeline.

Usage:
    python backend/scripts/ingest_events.py
"""

import sys
import os

# Add backend directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import init_db, SessionLocal
from app.services.pipeline import run_etl_pipeline
from app.utils.logger import log_info, log_error


def main() -> None:
    """Executes event data ETL pipeline from command line."""
    raw_csv = "data/raw/Week3_Task_3_raw_event_sample.csv"
    processed_csv = "data/processed/Week3_Task_3_standardised_event_sample.csv"
    validation_log = "data/validation_logs/Week3_Task_3_data_quality_validation_log.csv"

    print("==================================================")
    print("Starting Tourism Portal Event Ingestion Pipeline")
    print("==================================================")

    init_db()
    db = SessionLocal()

    try:
        results = run_etl_pipeline(raw_csv, processed_csv, validation_log, db)
        print("\n✅ ETL Ingestion Run Successful!")
        print(f" - Records Processed: {results['processed_count']}")
        print(f" - Quality Issues Logged: {results['validation_issues_count']}")
        print(f" - Processed Output CSV: {results['processed_csv']}")
        print(f" - Validation Log CSV:   {results['validation_log_csv']}")
    except Exception as e:
        log_error("main", "ETL Pipeline execution failed", error=e)
        print(f"\n❌ Error during ETL execution: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
