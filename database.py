import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

raw_url = os.getenv("DATABASE_URL")
db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "greek_real_estate")

if not raw_url and db_user and db_pass and db_host:
    raw_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

if raw_url:
    # Convert postgres:// to postgresql:// for SQLAlchemy 2.0 compatibility
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    if "?" in raw_url:
        raw_url = raw_url.split("?")[0]
    DATABASE_URL = raw_url
else:
    # Fallback to local SQLite database for instant cloud deployment
    db_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "app.db")
    DATABASE_URL = f"sqlite:///{db_path}"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 1}

try:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    with engine.connect() as conn:
        pass
except Exception:
    # Safe fallback if PostgreSQL connection is refused
    db_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "app.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        from models import Base as AppBase
        AppBase.metadata.create_all(bind=engine)
    except Exception:
        pass

# Ensure tables are created immediately
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
