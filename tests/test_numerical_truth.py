import pytest
from database import SessionLocal
import queries
from loader import GEOGRAPHICAL_REGIONS

def test_no_synthetic_regions():
    """Verify that no fabricated regional scaling multipliers exist in GEOGRAPHICAL_REGIONS."""
    slugs = [r["slug"] for r in GEOGRAPHICAL_REGIONS]
    assert "greece" not in slugs
    assert "thessaloniki" not in slugs
    assert "other-cities" not in slugs
    assert "other-areas" not in slugs
    assert slugs == ["athens"]

def test_no_duplicate_observations():
    """Verify that there are zero duplicate observations per geographical area and period date."""
    db = SessionLocal()
    try:
        rows = queries.get_price_indices(db, area_slugs=["athens"])
        dates = [r["periodDate"] for r in rows]
        assert len(dates) == len(set(dates)), "Duplicate observations found for the same quarter!"
    finally:
        db.close()

def test_correct_quarter_count():
    """Verify that totalQuarters matches the exact unique quarter count (79 quarters)."""
    db = SessionLocal()
    try:
        stats = queries.get_market_statistics(db, area_slugs=["athens"])
        assert stats is not None
        assert stats["totalQuarters"] == 79
    finally:
        db.close()

def test_qoq_formula_accuracy():
    """Verify that stored QoQ % matches ((Index_t / Index_{t-1}) - 1) * 100 exactly."""
    db = SessionLocal()
    try:
        rows = queries.get_price_indices(db, area_slugs=["athens"])
        for i in range(1, len(rows)):
            curr = rows[i]
            prev = rows[i-1]
            calc_qoq = round(((curr["priceIndex"] - prev["priceIndex"]) / prev["priceIndex"]) * 100.0, 4)
            stored_qoq = curr["periodChangePercent"]
            assert stored_qoq is not None
            assert abs(stored_qoq - calc_qoq) < 0.0001
    finally:
        db.close()

def test_yoy_formula_accuracy():
    """Verify that stored YoY % matches ((Index_t / Index_{t-4}) - 1) * 100 exactly."""
    db = SessionLocal()
    try:
        rows = queries.get_price_indices(db, area_slugs=["athens"])
        for i in range(4, len(rows)):
            curr = rows[i]
            prev_y = rows[i-4]
            calc_yoy = round(((curr["priceIndex"] - prev_y["priceIndex"]) / prev_y["priceIndex"]) * 100.0, 4)
            stored_yoy = curr["annualChangePercent"]
            assert stored_yoy is not None
            assert abs(stored_yoy - calc_yoy) < 0.0001
    finally:
        db.close()

def test_yearly_granularity_growth():
    """Verify that yearly YoY growth is computed from annual average indices rather than arithmetic means."""
    db = SessionLocal()
    try:
        yearly_rows = queries.get_price_indices(db, area_slugs=["athens"], granularity="yearly")
        assert len(yearly_rows) > 0
        for i in range(1, len(yearly_rows)):
            curr = yearly_rows[i]
            prev = yearly_rows[i-1]
            calc_annual_yoy = round(((curr["priceIndex"] - prev["priceIndex"]) / prev["priceIndex"]) * 100.0, 3)
            stored_yoy = curr["annualChangePercent"]
            assert stored_yoy is not None
            assert abs(stored_yoy - calc_annual_yoy) < 0.005
    finally:
        db.close()

def test_dynamic_market_insights():
    """Verify that dynamic market insights accurately derive peak, trough, and rebound percentages from DB."""
    db = SessionLocal()
    try:
        insights = queries.get_dynamic_market_insights(db, area_slug="athens")
        assert insights is not None
        assert insights["firstPeriod"] == "2006 Q1"
        assert insights["latestPeriod"] == "2025 Q3"
        assert "Q" in insights["peakPeriod"]
        assert "Q" in insights["troughPeriod"]
        assert insights["recessionDeclinePct"] < 0
        assert insights["recoveryReboundPct"] > 0
    finally:
        db.close()
