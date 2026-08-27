import time
from database import SessionLocal
import queries
from logger import logger

def profile_queries():
    db = SessionLocal()
    try:
        logger.info("--- STARTING QUERY PERFORMANCE PROFILER ---")

        # 1. Profile Areas query
        t0 = time.perf_counter()
        areas = queries.get_all_geographical_areas(db)
        t1 = time.perf_counter()
        logger.info(f"get_all_geographical_areas: {(t1 - t0)*1000:.2f}ms (Count: {len(areas)})")

        # 2. Profile Price Indices query
        t0 = time.perf_counter()
        rows = queries.get_price_indices(db, area_slugs=["athens"])
        t1 = time.perf_counter()
        logger.info(f"get_price_indices (Athens): {(t1 - t0)*1000:.2f}ms (Rows: {len(rows)})")

        # 3. Profile Summary Metrics query
        t0 = time.perf_counter()
        summary = queries.get_metrics_summary(db, area_slugs=["athens"])
        t1 = time.perf_counter()
        logger.info(f"get_metrics_summary: {(t1 - t0)*1000:.2f}ms (Latest: {summary.get('latestIndex')})")

        # 4. Profile Statistics query
        t0 = time.perf_counter()
        stats = queries.get_market_statistics(db, area_slugs=["athens"])
        t1 = time.perf_counter()
        logger.info(f"get_market_statistics: {(t1 - t0)*1000:.2f}ms (Max Index: {stats['highestIndex']['value']})")

        logger.info("--- PROFILING COMPLETED ---")
    finally:
        db.close()

if __name__ == "__main__":
    profile_queries()
