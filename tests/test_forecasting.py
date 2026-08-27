import pytest
from database import SessionLocal
from forecasting import generate_area_forecast

def test_generate_area_forecast():
    db = SessionLocal()
    try:
        res = generate_area_forecast(db, area_slug="athens", forecast_quarters=12)
        if res:
            assert "forecastData" in res
            assert len(res["forecastData"]) == 12
            assert "summary" in res
            assert res["summary"]["forecast1yIndex"] > 0
            assert "forecast3yIndex" in res["summary"]
            assert res["forecastData"][0]["lowerBound"] <= res["forecastData"][0]["upperBound"]
    finally:
        db.close()
