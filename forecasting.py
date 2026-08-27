import math
from datetime import datetime
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
import queries

def generate_area_forecast(db: Session, area_slug: str = "athens", forecast_quarters: int = 12):
    """
    Fits a time-series forecasting model (Exponential Smoothing / ARIMA)
    on historical Bank of Greece price index data for a given geographical area.
    
    Returns point forecasts and 95% confidence bounds for 1 to 3 years (4-12 quarters ahead).
    """
    # Fetch historical quarterly indices
    records = queries.get_price_indices(db, area_slugs=[area_slug], granularity="quarterly")
    if not records:
        return None
    
    df = pd.DataFrame(records)
    if df.empty or len(df) < 8:
        return None
    
    # Sort chronologically by periodDate
    df = df.sort_values('periodDate').reset_index(drop=True)
    
    # Extract timeseries values
    ts_data = df['priceIndex'].values.astype(float)
    dates = pd.to_datetime(df['periodDate'])
    
    latest_row = df.iloc[-1]
    latest_index = float(latest_row['priceIndex'])
    latest_year = int(latest_row['year'])
    latest_quarter_raw = str(latest_row['quarter'])
    
    try:
        latest_q = int(latest_quarter_raw)
    except ValueError:
        latest_q = 4

    # Fit Holt's Linear Exponential Smoothing model
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        model = ExponentialSmoothing(ts_data, trend='add', seasonal=None, initialization_method="estimated")
        fitted_model = model.fit()
        predictions = fitted_model.forecast(forecast_quarters)
        
        # Calculate residual variance for confidence bounds
        residuals = fitted_model.resid
        std_err = np.std(residuals) if len(residuals) > 0 else 2.0
    except Exception:
        # Robust Fallback: Linear Trend Regression if statsmodels fails or is fitting
        x = np.arange(len(ts_data))
        slope, intercept = np.polyfit(x, ts_data, 1)
        future_x = np.arange(len(ts_data), len(ts_data) + forecast_quarters)
        predictions = slope * future_x + intercept
        residuals = ts_data - (slope * x + intercept)
        std_err = np.std(residuals)

    # Generate future quarters timeline & confidence bounds
    forecast_list = []
    curr_y = latest_year
    curr_q = latest_q
    
    for i, pred_val in enumerate(predictions):
        curr_q += 1
        if curr_q > 4:
            curr_q = 1
            curr_y += 1
            
        period_label = f"{curr_y} Q{curr_q}"
        pred_clean = round(float(pred_val), 1)
        
        # Expanding confidence interval over forecast horizon (95% CI multiplier = 1.96)
        horizon_multiplier = math.sqrt(i + 1)
        margin = round(1.96 * std_err * horizon_multiplier, 1)
        lower_bound = round(max(0.0, pred_clean - margin), 1)
        upper_bound = round(pred_clean + margin, 1)
        
        cum_growth = round(((pred_clean - latest_index) / latest_index) * 100, 1) if latest_index > 0 else 0.0
        
        forecast_list.append({
            "step": i + 1,
            "year": curr_y,
            "quarter": curr_q,
            "periodLabel": period_label,
            "forecastIndex": pred_clean,
            "lowerBound": lower_bound,
            "upperBound": upper_bound,
            "cumulativeGrowthPct": cum_growth
        })
    
    # 1-Year (4 Quarters) & 3-Year (12 Quarters) Summary KPIs
    f_1y = forecast_list[min(3, len(forecast_list) - 1)]
    f_3y = forecast_list[-1]
    
    summary = {
        "latestIndex": latest_index,
        "latestPeriod": f"{latest_year} Q{latest_q}",
        "forecast1yIndex": f_1y["forecastIndex"],
        "forecast1yGrowthPct": f_1y["cumulativeGrowthPct"],
        "forecast3yIndex": f_3y["forecastIndex"],
        "forecast3yGrowthPct": f_3y["cumulativeGrowthPct"],
        "modelType": "Holt's Linear Exponential Smoothing"
    }
    
    return {
        "areaSlug": area_slug,
        "areaName": latest_row['areaName'],
        "historicalData": df[['periodDate', 'year', 'quarter', 'priceIndex']].to_dict(orient='records'),
        "forecastData": forecast_list,
        "summary": summary
    }
