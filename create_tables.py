from sqlalchemy import text
from database import engine, Base
import models
from logger import logger

def init_db():
    logger.info("Creating database tables via SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

    view_sql = """
    CREATE OR REPLACE VIEW latest_price_indices AS
    SELECT DISTINCT ON (p.geographical_area_id, p.period_date)
      p.id,
      p.geographical_area_id,
      p.dataset_resource_id,
      p.period_date,
      p.year,
      p.quarter,
      p.price_index,
      p.period_change_percent,
      p.annual_change_percent,
      p.is_provisional,
      p.created_at,
      p.updated_at,
      r.resource_name,
      r.resource_date
    FROM price_indices p
    JOIN dataset_resources r ON p.dataset_resource_id = r.id
    ORDER BY p.geographical_area_id, p.period_date, r.resource_date DESC;
    """

    with engine.connect() as conn:
        conn.execute(text(view_sql))
        conn.commit()
    logger.info("View 'latest_price_indices' initialized successfully.")

if __name__ == "__main__":
    init_db()
