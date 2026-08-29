import io
import csv
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, Depends, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, engine
import models
from queries import (
    get_all_geographical_areas,
    get_price_indices,
    get_metrics_summary,
    get_market_statistics
)
from loader import import_all, import_single_resource
from logger import logger

app = FastAPI(
    title="Greek Real Estate Analytics API",
    description="Official Bank of Greece Apartment Price Index API Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    models.Base.metadata.create_all(bind=engine)
    logger.info("FastAPI service started successfully.")

@app.get("/")
def read_root():
    return {
        "service": "Greek Real Estate Market Analytics API",
        "dataset_source": "Bank of Greece",
        "documentation": "/docs",
        "status": "online"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/areas")
def api_get_areas(db: Session = Depends(get_db)):
    areas = get_all_geographical_areas(db)
    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "name": a.name,
                "slug": a.slug,
                "area_type": a.area_type,
                "source_code": a.source_code
            }
            for a in areas
        ]
    }

@app.get("/api/price-indices")
def api_get_price_indices(
    areaIds: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    granularity: str = Query("quarterly"),
    provisional: str = Query("all"),
    db: Session = Depends(get_db)
):
    area_slugs = areaIds.split(",") if areaIds else None
    start_dt = datetime.strptime(startDate, "%Y-%m-%d") if startDate else None
    end_dt = datetime.strptime(endDate, "%Y-%m-%d") if endDate else None

    data = get_price_indices(
        db,
        area_slugs=area_slugs,
        start_date=start_dt,
        end_date=end_dt,
        granularity=granularity,
        provisional_filter=provisional
    )
    return {"success": True, "count": len(data), "data": data}

@app.get("/api/metrics/summary")
def api_get_metrics_summary(
    areaIds: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    area_slugs = areaIds.split(",") if areaIds else None
    start_dt = datetime.strptime(startDate, "%Y-%m-%d") if startDate else None
    end_dt = datetime.strptime(endDate, "%Y-%m-%d") if endDate else None

    data = get_metrics_summary(db, area_slugs=area_slugs, start_date=start_dt, end_date=end_dt)
    return {"success": True, "data": data}

@app.get("/api/statistics")
def api_get_statistics(
    areaIds: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    area_slugs = areaIds.split(",") if areaIds else None
    start_dt = datetime.strptime(startDate, "%Y-%m-%d") if startDate else None
    end_dt = datetime.strptime(endDate, "%Y-%m-%d") if endDate else None

    data = get_market_statistics(db, area_slugs=area_slugs, start_date=start_dt, end_date=end_dt)
    return {"success": True, "data": data}

@app.get("/api/resources")
def api_get_resources(db: Session = Depends(get_db)):
    data_source = db.query(models.DataSource).first()
    if not data_source:
        return {"success": True, "data": None}

    resources = db.query(models.DatasetResource).order_by(models.DatasetResource.resource_date.desc()).all()
    completed_count = sum(1 for r in resources if r.import_status == "completed")

    return {
        "success": True,
        "data": {
            "dataSource": {
                "id": data_source.id,
                "name": data_source.name,
                "organization": data_source.organization,
                "datasetName": data_source.dataset_name,
                "datasetIdentifier": data_source.dataset_identifier,
                "datasetUrl": data_source.dataset_url,
                "license": data_source.license,
                "description": data_source.description,
                "resources": [
                    {
                        "id": r.id,
                        "resourceName": r.resource_name,
                        "resourceUrl": r.resource_url,
                        "resourceDate": r.resource_date.isoformat(),
                        "fileFormat": r.file_format,
                        "importStatus": r.import_status,
                        "importedAt": r.imported_at.isoformat() if r.imported_at else None
                    }
                    for r in resources
                ]
            },
            "totalResources": len(resources),
            "completedResources": completed_count
        }
    }

@app.post("/api/import")
def api_trigger_import():
    try:
        import_all()
        return {"success": True, "message": "ETL ingestion completed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export")
def api_export_csv(
    areaIds: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    provisional: str = Query("all"),
    db: Session = Depends(get_db)
):
    area_slugs = areaIds.split(",") if areaIds else None
    start_dt = datetime.strptime(startDate, "%Y-%m-%d") if startDate else None
    end_dt = datetime.strptime(endDate, "%Y-%m-%d") if endDate else None

    rows = get_price_indices(
        db,
        area_slugs=area_slugs,
        start_date=start_dt,
        end_date=end_dt,
        granularity="quarterly",
        provisional_filter=provisional
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Geographical Area", "Year", "Quarter", "Period",
        "Price Index", "QoQ Change %", "YoY Change %", "Provisional", "Source Resource"
    ])

    for r in rows:
        writer.writerow([
            r["areaName"],
            r["year"],
            r["quarter"],
            f"{r['year']} Q{r['quarter']}",
            r["priceIndex"],
            r["periodChangePercent"] if r["periodChangePercent"] is not None else "",
            r["annualChangePercent"] if r["annualChangePercent"] is not None else "",
            "Yes" if r["isProvisional"] else "No",
            r.get("resourceName", "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=greek_real_estate_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@app.get("/api/forecast")
def api_get_forecast(
    areaId: str = Query("athens"),
    quarters: int = Query(12, ge=1, le=20),
    db: Session = Depends(get_db)
):
    from forecasting import generate_area_forecast
    res = generate_area_forecast(db, area_slug=areaId, forecast_quarters=quarters)
    if not res:
        raise HTTPException(status_code=404, detail=f"No price index data available for forecast area: {areaId}")
    return {"success": True, "data": res}

@app.get("/api/export/pdf")
def api_export_pdf(
    lang: str = Query("en"),
    db: Session = Depends(get_db)
):
    from report_generator import generate_pdf_report
    pdf_bytes = generate_pdf_report(db, lang=lang)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=greek_real_estate_executive_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        }
    )


