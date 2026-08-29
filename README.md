# 🏛️ Greek Real Estate Market Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25%2B-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.0%2B-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

An end-to-end, production-grade financial analytics platform and REST API for visualizing, analyzing, and querying official **Bank of Greece** apartment price index data.

> 🇬🇷 **Ελληνικά**: Πλατφόρμα ανάλυσης και οπτικοποίησης δεδομένων δεικτών τιμών διαμερισμάτων της **Τράπεζας της Ελλάδος**. Προσφέρει διαδραστικό dashboard (Streamlit), REST API (FastAPI) και πλήρη μηχανή ETL.

---

## 🌐 Live Demo & Deployment
🔗 **Public Application URL:** [https://greek-real-estate-analytics.onrender.com](https://greek-real-estate-analytics.onrender.com)

---

## 🌟 Key Features

* **📊 Interactive Financial Dashboard**: Streamlit dashboard powered by Plotly charts, customizable color palettes, and responsive glassmorphism UI.
* **🔮 ML Price Index Forecasting**: Time-series forecasting module (`forecasting.py`) utilizing Holt's Linear Exponential Smoothing to project apartment price indices 1–3 years into the future with 95% confidence intervals.
* **🗺️ Interactive GeoJSON Regional Map**: Plotly Choropleth map visualizing price index valuations and YoY growth rates across Greek administrative regions.
* **🧮 Investor ROI & Mortgage Calculator**: Dedicated financial calculator module (`calculator.py`) for computing Net Cap Rate, Gross Yield, ENFIA property taxes, monthly mortgage payments, and annual amortization schedules.
* **📄 Executive PDF Report Generator**: Automated ReportLab PDF generator (`report_generator.py`) for exporting formatted executive summaries with one-click dashboard download & `/api/export/pdf` REST endpoint.
* **🌐 Bilingual Interface**: Native support for **English 🇬🇧** and **Greek 🇬🇷** localization.
* **🚀 Production REST API**: High-performance FastAPI endpoints for geographic areas, price indices, ML forecasts (`/api/forecast`), PDF exports (`/api/export/pdf`), and revision logs.
* **⚡ Automated ETL Engine**: Robust loader (`loader.py`) parsing official Bank of Greece XLS resources.
* **🗄️ Normalized Relational Database**: PostgreSQL architecture designed with 5 normalized tables and Alembic migrations.
* **🐳 Docker Orchestration**: Complete containerized environment using Docker Compose.
* **🧪 Comprehensive Testing & Profiling**: Pytest coverage for ETL routines, API endpoints, forecasting, calculator, and PDF generation.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph ExternalSources["External Data Sources"]
        BoG["Bank of Greece Official XLS Resources<br/>(62 Dataset Resources)"]
        Meta["datapackage.json<br/>(Source Metadata Specifications)"]
    end

    subgraph ETLPipeline["Data Pipeline & ETL"]
        APIClient["api_client.py<br/>(API Fetcher & Retry Engine)"]
        Schemas["schemas.py<br/>(Pydantic Schema Validation)"]
        Loader["loader.py<br/>(Transform & Ingestion)"]
        Fallback["data/downloads<br/>(Local File Cache / Fallback)"]
    end

    subgraph DBLayer["Database Layer"]
        Postgres[("PostgreSQL Database<br/>(Indexes: year, date_key, area_id)")]
        Queries["queries.py<br/>(Window Functions: YoY/QoQ LAG, Revision Views)"]
    end

    subgraph BackendAPI["Backend API Layer"]
        FastAPI["main.py<br/>(FastAPI REST Server & OpenAPI Docs)"]
    end

    subgraph UILayer["Presentation & UI Layer"]
        Cache["@st.cache_data (TTL=3600s)<br/>@st.cache_resource"]
        i18n["i18n.py<br/>(Bilingual EN / EL Support)"]
        Dashboard["dashboard.py<br/>(Streamlit Financial Dashboard)"]
        
        Trends["Price Index Trends 📈"]
        Regional["Regional Analytics 🗺️"]
        Growth["YoY / QoQ Growth Rates 📊"]
        Revisions["Revision History & Insights 📑"]
    end

    BoG --> APIClient
    Meta --> Schemas
    APIClient --> Loader
    Schemas --> Loader
    Loader -.->|"Failure Fallback"| Fallback
    Fallback -.-> Loader
    Loader --> Postgres

    Postgres --> Queries
    Queries --> FastAPI
    Queries --> Cache

    Cache --> Dashboard
    i18n --> Dashboard

    Dashboard --> Trends
    Dashboard --> Regional
    Dashboard --> Growth
    Dashboard --> Revisions
```

---

## 📁 Repository Directory Structure

```
GreekRealEstateAnalytics/
├── .streamlit/
│   └── config.toml           # Streamlit custom UI & dark theme configuration
├── alembic/
│   ├── env.py                # Database migration environment configuration
│   └── versions/             # Database migration version scripts
├── data/
│   └── datapackage.json      # Official Bank of Greece dataset source metadata
├── tests/
│   ├── test_api.py           # FastAPI endpoint test suite
│   ├── test_loader.py        # ETL parser unit tests
│   └── test_models.py        # Database models & query tests
├── .env.example              # Template environment variable configuration
├── .gitignore                # Git ignore rules for virtualenvs, logs & credentials
├── alembic.ini               # Alembic migration engine configuration
├── api_client.py             # Python client utility for consuming the REST API
├── app.log                   # Application logging output
├── create_tables.py          # PostgreSQL schema and SQL views initializer
├── dashboard.py              # Interactive Streamlit analytics web application
├── database.py               # SQLAlchemy database engine and session manager
├── docker-compose.yml        # Docker Compose configuration (Postgres, API, UI)
├── Dockerfile                # Multi-stage Docker build configuration
├── i18n.py                   # Internationalization module (EN / EL localization)
├── loader.py                 # Core ETL pipeline for XLS ingestion
├── logger.py                 # Centralized logging module
├── main.py                   # FastAPI application server entrypoint
├── models.py                 # SQLAlchemy ORM models (5 normalized entities)
├── profiler.py               # Database query performance benchmarking tool
├── pyproject.toml            # Project metadata and tooling configuration
├── pytest.ini                # Pytest configuration settings
├── queries.py                # Database query layer & view handlers
├── README.md                 # Project documentation
├── requirements.txt          # Production Python dependencies
└── schemas.py                # Pydantic models for API request/response serialization
```

---

## 🚀 Setup & Installation

### 1. Local Run

**Prerequisites:**
* Python 3.10+
* Running PostgreSQL instance (or Docker Postgres fallback)

**Steps:**

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/tsakirisand/Greek-Real-Estate-Analytics-.git
   cd Greek-Real-Estate-Analytics-
   ```

2. **Create & Activate Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables (`.env`):**
   Create a `.env` file in the project root directory (or copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Example configuration:
   ```env
   DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5433/greek_real_estate?schema=public"
   ```

5. **Initialize Database & Load Data:**
   ```bash
   # Create database tables and latest_price_indices SQL views
   python3 create_tables.py

   # Extract Bank of Greece dataset resources and load into PostgreSQL
   python3 loader.py
   ```

6. **Launch Applications:**
   ```bash
   # Launch Streamlit Analytics Dashboard
   streamlit run dashboard.py --server.port 8501

   # Launch FastAPI REST Service
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   * Access the dashboard at **[http://localhost:8501](http://localhost:8501)**.
   * Access interactive API docs at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### 2. Run with Docker Compose

```bash
docker-compose up --build
```
* Access the dashboard at **[http://localhost:8501](http://localhost:8501)**.
* Access the REST API at **[http://localhost:8000](http://localhost:8000)** (Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**).

---

## 🔗 REST API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root endpoint displaying service health and dataset info |
| `GET` | `/health` | Application health check status |
| `GET` | `/api/areas` | Retrieve list of all available geographical regions |
| `GET` | `/api/price-indices` | Fetch filtered price index timeseries (quarterly/annual) |
| `GET` | `/api/metrics/summary` | Summary statistics (min, max, average, latest index) |
| `GET` | `/api/market-statistics` | Comprehensive YoY/QoQ growth rates across areas |
| `GET` | `/api/revisions` | Revision audit log for price index updates |
| `GET` | `/api/export/csv` | Download filtered datasets in CSV format |
| `GET` | `/api/forecast` | ML Holt's exponential smoothing forecast by area |
| `GET` | `/api/export/pdf` | Download formatted executive PDF report |

---

## 🧪 Running Unit Tests Locally

Run the complete pytest suite with test coverage reporting:

```bash
# Run pytest with summary
pytest

# Run pytest with code coverage breakdown
pytest --cov=. --cov-report=term-missing
```

Run code formatting and security audit checks:

```bash
# Check code formatting (Black)
black --check .

# Run linting (Flake8)
flake8 .

# Run security static analysis (Bandit)
bandit -r . -x ./tests,./venv

# Run database query performance benchmarks
python3 profiler.py
```

---

## 📜 Data Attribution & References

Data source provided by the **Bank of Greece** (*Τράπεζα της Ελλάδος*) — Real Estate Market Analysis Section.
Dataset definitions and metadata adhere to `datapackage.json` standards.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
