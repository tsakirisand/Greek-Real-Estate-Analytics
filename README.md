# Greek Real Estate Market Analytics Platform

A production-grade financial analytics platform for visualizing official **Bank of Greece** apartment price index data.

## 📁 Repository File Layout

```
GreekRealEstateAnalytics/
├── .streamlit/
│   └── config.toml           # Streamlit dark theme settings
├── alembic/
│   ├── env.py                # Database migration environment
│   └── versions/             # Migration versions
├── data/
│   └── datapackage.json      # Bank of Greece source metadata
├── tests/
│   ├── test_api.py           # FastAPI endpoint tests
│   ├── test_loader.py        # ETL parser unit tests
│   └── test_models.py        # Database query tests
├── venv/                     # Python virtual environment
├── .env                      # Database configuration
├── alembic.ini               # Alembic configuration
├── api_client.py             # Python client helper
├── app.log                   # Application audit log
├── create_tables.py          # Table & SQL view initializer
├── dashboard.py              # Streamlit interactive analytics web app
├── database.py               # SQLAlchemy engine & session factory
├── docker-compose.yml        # Docker orchestration (PostgreSQL, FastAPI, Streamlit)
├── Dockerfile                # Python container image build file
├── loader.py                 # Python ETL loader (parses all 62 XLS files)
├── logger.py                 # Centralized logging setup
├── main.py                   # FastAPI REST application server
├── models.py                 # SQLAlchemy ORM models (5 normalized tables)
├── profiler.py               # Query performance profiling script
├── pyproject.toml            # Project build metadata
├── pytest.ini                # Pytest configuration
├── queries.py                # Database queries & revision view handlers
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
└── schemas.py                # Pydantic schemas
```

---

## ⚡ Quick Start (Local Setup)

### 1. Initialize Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. Initialize Database & Run Ingestion
```bash
# Create PostgreSQL tables and latest_price_indices SQL view
./venv/bin/python3 create_tables.py

# Download and parse all 62 Bank of Greece XLS resources
./venv/bin/python3 loader.py
```

### 3. Launch Streamlit Analytics Dashboard
```bash
./venv/bin/streamlit run dashboard.py --server.port 8501
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

### 4. Launch FastAPI REST Server
```bash
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```
API Documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 🐳 Docker Deployment

To launch PostgreSQL, FastAPI, and Streamlit in Docker containers:
```bash
docker-compose up --build
```

---

## 🧪 Testing & Profiling

Run unit tests:
```bash
./venv/bin/python -m pytest
```

Profile query execution speeds:
```bash
./venv/bin/python3 profiler.py
```
