from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import GeographicalArea, DataSource, DatasetResource, ImportLog

def get_all_geographical_areas(db: Session):
    return db.query(GeographicalArea).order_by(GeographicalArea.name.asc()).all()

def get_price_indices(
    db: Session,
    area_slugs: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "quarterly",
    provisional_filter: str = "all"
):
    params: Dict[str, Any] = {}
    where_clauses = ["1=1"]

    if start_date:
        where_clauses.append("p.period_date >= :start_date")
        params["start_date"] = start_date

    if end_date:
        where_clauses.append("p.period_date <= :end_date")
        params["end_date"] = end_date

    if area_slugs and len(area_slugs) > 0:
        where_clauses.append("g.slug = ANY(:area_slugs)")
        params["area_slugs"] = area_slugs

    if provisional_filter == "provisional_only":
        where_clauses.append("p.is_provisional = True")
    elif provisional_filter == "final_only":
        where_clauses.append("p.is_provisional = False")

    where_sql = " AND ".join(where_clauses)

    sql = f"""
    SELECT 
      p.id,
      p.geographical_area_id AS geographicalareaid,
      g.name AS areaname,
      g.slug AS areaslug,
      p.period_date AS perioddate,
      p.year,
      p.quarter,
      p.price_index AS priceindex,
      p.period_change_percent AS periodchangepercent,
      p.annual_change_percent AS annualchangepercent,
      p.is_provisional AS isprovisional,
      p.resource_name AS resourcename
    FROM latest_price_indices p
    JOIN geographical_areas g ON p.geographical_area_id = g.id
    WHERE {where_sql}
    ORDER BY p.period_date ASC;
    """

    result = db.execute(text(sql), params)
    raw_rows = [dict(row._mapping) for row in result]

    rows = []
    for r in raw_rows:
        rows.append({
            "id": r["id"],
            "geographicalAreaId": r["geographicalareaid"],
            "areaName": r["areaname"],
            "areaSlug": r["areaslug"],
            "periodDate": r["perioddate"],
            "year": r["year"],
            "quarter": r["quarter"],
            "priceIndex": float(r["priceindex"]),
            "periodChangePercent": float(r["periodchangepercent"]) if r["periodchangepercent"] is not None else None,
            "annualChangePercent": float(r["annualchangepercent"]) if r["annualchangepercent"] is not None else None,
            "isProvisional": bool(r["isprovisional"]),
            "resourceName": r["resourcename"] if r["resourcename"] else "Bank of Greece XLS"
        })

    if granularity == "yearly":
        yearly_map = {}
        for r in rows:
            key = f"{r['areaSlug']}-{r['year']}"
            if key not in yearly_map:
                yearly_map[key] = {
                    "year": r["year"],
                    "areaName": r["areaName"],
                    "areaSlug": r["areaSlug"],
                    "geographicalAreaId": r["geographicalAreaId"],
                    "indices": [],
                    "qoq_changes": [],
                    "yoy_changes": [],
                    "is_provisional": False,
                    "resourceName": r["resourceName"]
                }
            item = yearly_map[key]
            item["indices"].append(float(r["priceIndex"]))
            if r["periodChangePercent"] is not None:
                item["qoq_changes"].append(float(r["periodChangePercent"]))
            if r["annualChangePercent"] is not None:
                item["yoy_changes"].append(float(r["annualChangePercent"]))
            if r["isProvisional"]:
                item["is_provisional"] = True

        yearly_rows = []
        for k, v in yearly_map.items():
            avg_idx = sum(v["indices"]) / len(v["indices"])
            avg_qoq = sum(v["qoq_changes"]) / len(v["qoq_changes"]) if v["qoq_changes"] else None
            avg_yoy = sum(v["yoy_changes"]) / len(v["yoy_changes"]) if v["yoy_changes"] else None
            yearly_rows.append({
                "id": f"yearly-{v['areaSlug']}-{v['year']}",
                "geographicalAreaId": v["geographicalAreaId"],
                "areaName": v["areaName"],
                "areaSlug": v["areaSlug"],
                "periodDate": datetime(v["year"], 1, 1),
                "year": v["year"],
                "quarter": "Annual Avg",
                "priceIndex": round(avg_idx, 3),
                "periodChangePercent": round(avg_qoq, 3) if avg_qoq is not None else None,
                "annualChangePercent": round(avg_yoy, 3) if avg_yoy is not None else None,
                "isProvisional": v["is_provisional"],
                "resourceName": v["resourceName"],
                "isDerivedYearlyAvg": True,
            })
        return yearly_rows

    return rows

def get_metrics_summary(
    db: Session,
    area_slugs: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    granularity: str = "quarterly"
):
    rows = get_price_indices(db, area_slugs=area_slugs, start_date=start_date, end_date=end_date, granularity=granularity)
    if not rows:
        return {
            "latestIndex": 0,
            "latestQuarter": "N/A",
            "latestYear": 0,
            "firstPeriod": "N/A",
            "qoqChange": None,
            "yoyChange": None,
            "cumulativeChange": 0,
            "isProvisional": False,
            "marketDirection": "Stable"
        }

    rows_sorted = sorted(rows, key=lambda x: x["periodDate"])
    latest = rows_sorted[-1]
    first = rows_sorted[0]

    latest_index = latest["priceIndex"]
    first_index = first["priceIndex"]
    cum_change = ((latest_index - first_index) / first_index) * 100.0 if first_index > 0 else 0.0

    qoq_change = latest.get("periodChangePercent")
    yoy_change = latest.get("annualChangePercent")

    if granularity == "yearly":
        latest_period_str = f"{latest['year']} ΜΟ" if "Annual" in str(latest.get('quarter', '')) else f"{latest['year']}"
        first_period_str = f"{first['year']}"
    else:
        latest_period_str = f"{latest['year']} Q{latest['quarter']}"
        first_period_str = f"{first['year']} Q{first['quarter']}"

    if len(rows_sorted) >= 2:
        prev = rows_sorted[-2]
        diff = latest_index - prev["priceIndex"]
        if diff > 0.5:
            direction = "Rising"
        elif diff < -0.5:
            direction = "Falling"
        else:
            direction = "Stable"
    else:
        direction = "Stable"

    return {
        "latestIndex": round(latest_index, 2),
        "latestQuarter": latest_period_str,
        "latestYear": latest["year"],
        "firstPeriod": first_period_str,
        "qoqChange": round(float(qoq_change), 2) if qoq_change is not None else None,
        "yoyChange": round(float(yoy_change), 2) if yoy_change is not None else None,
        "cumulativeChange": round(cum_change, 2),
        "isProvisional": bool(latest.get("isProvisional", False)),
        "marketDirection": direction
    }

def get_market_statistics(
    db: Session,
    area_slugs: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    rows = get_price_indices(db, area_slugs=area_slugs, start_date=start_date, end_date=end_date)
    if not rows:
        return None

    highest_idx = max(rows, key=lambda r: float(r["priceIndex"]))
    lowest_idx = min(rows, key=lambda r: float(r["priceIndex"]))

    valid_qoq = [r for r in rows if r["periodChangePercent"] is not None]
    highest_qoq = max(valid_qoq, key=lambda r: float(r["periodChangePercent"])) if valid_qoq else rows[0]
    lowest_qoq = min(valid_qoq, key=lambda r: float(r["periodChangePercent"])) if valid_qoq else rows[0]

    valid_yoy = [r for r in rows if r["annualChangePercent"] is not None]
    highest_yoy = max(valid_yoy, key=lambda r: float(r["annualChangePercent"])) if valid_yoy else rows[0]
    lowest_yoy = min(valid_yoy, key=lambda r: float(r["annualChangePercent"])) if valid_yoy else rows[0]

    return {
        "totalQuarters": len(rows),
        "firstPeriod": f"{rows[0]['year']} Q{rows[0]['quarter']}",
        "latestPeriod": f"{rows[-1]['year']} Q{rows[-1]['quarter']}",
        "highestIndex": {
            "value": float(highest_idx["priceIndex"]),
            "period": f"{highest_idx['year']} Q{highest_idx['quarter']}",
            "areaName": highest_idx["areaName"]
        },
        "lowestIndex": {
            "value": float(lowest_idx["priceIndex"]),
            "period": f"{lowest_idx['year']} Q{lowest_idx['quarter']}",
            "areaName": lowest_idx["areaName"]
        },
        "highestQoQIncrease": {
            "value": float(highest_qoq["periodChangePercent"]) if highest_qoq["periodChangePercent"] is not None else 0,
            "period": f"{highest_qoq['year']} Q{highest_qoq['quarter']}",
            "areaName": highest_qoq["areaName"]
        },
        "largestQoQDecrease": {
            "value": float(lowest_qoq["periodChangePercent"]) if lowest_qoq["periodChangePercent"] is not None else 0,
            "period": f"{lowest_qoq['year']} Q{lowest_qoq['quarter']}",
            "areaName": lowest_qoq["areaName"]
        },
        "highestYoYIncrease": {
            "value": float(highest_yoy["annualChangePercent"]) if highest_yoy["annualChangePercent"] is not None else 0,
            "period": f"{highest_yoy['year']} Q{highest_yoy['quarter']}",
            "areaName": highest_yoy["areaName"]
        },
        "largestYoYDecrease": {
            "value": float(lowest_yoy["annualChangePercent"]) if lowest_yoy["annualChangePercent"] is not None else 0,
            "period": f"{lowest_yoy['year']} Q{lowest_yoy['quarter']}",
            "areaName": lowest_yoy["areaName"]
        }
    }
