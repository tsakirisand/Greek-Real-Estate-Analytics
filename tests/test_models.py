from database import SessionLocal
from queries import get_all_geographical_areas, get_metrics_summary

def test_database_queries():
    db = SessionLocal()
    try:
        areas = get_all_geographical_areas(db)
        assert isinstance(areas, list)

        summary = get_metrics_summary(db, area_slugs=["athens"])
        assert "latestIndex" in summary
        assert "marketDirection" in summary
    finally:
        db.close()
