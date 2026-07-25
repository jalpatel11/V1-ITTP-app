# Tourism Discovery Portal - Backend API & Data Pipeline

Backend repository for the Bow and Red Deer River Corridors Tourism and Entertainment Discovery Portal pilot. Built using **Python**, **FastAPI**, **SQLAlchemy**, and **Pydantic**.

---

## 📁 Repository Structure

```text
.
├── app/
│   ├── main.py              # FastAPI entry point (/health, /api/* routes)
│   ├── config.py            # Environment configuration module
│   ├── database.py          # SQLAlchemy setup & connection
│   ├── models/
│   │   └── domain.py        # SQLAlchemy ORM domain models
│   ├── schemas/
│   │   └── domain.py        # Pydantic request/response schemas
│   ├── routes/              # API Route Controllers (/api/*)
│   │   ├── health.py        # Health check endpoint (/health)
│   │   ├── events.py        # GET /api/events, GET /api/events/{id}, GET /api/events/search
│   │   ├── map.py           # GET /api/map/events
│   │   ├── dashboard.py     # GET /api/dashboard/summary
│   │   ├── communities.py   # GET /api/communities
│   │   ├── categories.py    # GET /api/categories
│   │   └── quality.py       # GET /api/data-quality/issues
│   ├── services/
│   │   └── pipeline.py      # Data cleaning, validation log generation, & DB ETL
│   └── utils/
│       └── logger.py        # Contextual logging utility
├── scripts/
│   └── ingest_events.py     # Standalone CLI data ingestion pipeline script
├── tests/
│   └── test_backend.py      # Automated Pytest suite (9 tests)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment configuration template
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart & Setup

### 1. Environment Setup
Create a virtual environment and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template `.env.example` to `.env`:

```bash
cp .env.example .env
```

Default settings connect to an embedded SQLite database (`sqlite:///./tourism_portal.db`). PostgreSQL/PostGIS is supported by supplying a PostgreSQL connection string in `DATABASE_URL`:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/tourism_db"
```

---

## 📊 Data Ingestion Pipeline Execution

Run the standalone ingestion script to parse, clean, and validate raw sample data:

```bash
python scripts/ingest_events.py
```

This pipeline performs:
- **Text & Field Standardisation**: Normalises event titles, venues, dates (`YYYY-MM-DD`), and start/end times (`HH:MM`).
- **Data Quality Checks**: Flags missing titles, missing start dates, unlisted venues, expired events, missing geocoding coordinates, and duplicate risks.
- **Database Seeding**: Populates database tables (`corridors`, `communities`, `data_sources`, `venues`, `events`, `data_quality_issues`).

---

## 🖥️ Running the FastAPI Development Server

Start the API server locally on port 8000 (or 8008):

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive OpenAPI documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 📡 Core API Endpoints

All application endpoints are prefixed with `/api/*` (except `/health`):

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Health check endpoint |
| `/api/events` | `GET` | Paginated event list (supports `community`, `corridor`, `category`, `start_date`, `verification_status`) |
| `/api/events/{event_id}` | `GET` | Event detail lookup |
| `/api/events/search` | `GET` | Keyword search in title, description, or municipality (`?q=keyword`) |
| `/api/map/events` | `GET` | Geo-coordinate markers payload for map display |
| `/api/dashboard/summary` | `GET` | Municipality dashboard preview summary metrics |
| `/api/communities` | `GET` | List of active communities and event counts |
| `/api/categories` | `GET` | Supported event categories and counts |
| `/api/data-quality/issues` | `GET` | Data quality validation issues feed |

---

## 🧪 Running Unit Tests

Run the automated test suite with `pytest`:

```bash
pytest tests/
```
