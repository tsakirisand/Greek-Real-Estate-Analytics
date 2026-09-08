import os
import json
import re
import math
from datetime import datetime
import requests
import xlrd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import DataSource, DatasetResource, GeographicalArea, PriceIndex, ImportLog
from logger import logger

def parse_number(val):
    if val is None or val == "" or val == ":" or val == "-":
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val):
            return None
        return float(val)
    try:
        val_str = str(val).replace(",", ".").strip()
        parsed = float(val_str)
        return None if math.isnan(parsed) else parsed
    except ValueError:
        return None

def download_or_get_local_file(url: str, local_name: str) -> str:
    downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    file_path = os.path.join(downloads_dir, local_name)

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    # Check fallback path in data/downloads
    fallback_path = os.path.join(os.path.dirname(__file__), "data", "downloads", local_name)
    if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
        return fallback_path

    logger.info(f"Downloading resource from {url} -> {file_path}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except Exception as e:
        logger.warning(f"Download failed for {url} ({e}). Searching local files...")
        if os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 0:
            return fallback_path
        raise e

# Greek Geographical Regions definitions (Official Bank of Greece Series)
GEOGRAPHICAL_REGIONS = [
    {"name": "Athens (Αθήνα)", "slug": "athens", "type": "city", "code": "ATH"},
]

def parse_xls_file(file_path: str):
    workbook = xlrd.open_workbook(file_path)
    sheet = workbook.sheet_by_index(0)

    if sheet.nrows < 2:
        return [], []

    raw_observations = []

    for r in range(1, sheet.nrows):
        row = [sheet.cell_value(r, c) for c in range(sheet.ncols)]
        if len(row) < 3:
            continue

        raw_year = parse_number(row[0])
        raw_quarter = parse_number(row[1])
        base_price_index = parse_number(row[2])

        if not raw_year or not raw_quarter or base_price_index is None:
            continue

        year = int(round(raw_year))
        quarter = int(round(raw_quarter))

        if quarter < 1 or quarter > 4:
            continue

        month = (quarter - 1) * 3 + 1
        period_date = datetime(year, month, 1)

        base_qoq = parse_number(row[3]) if len(row) > 3 else None
        base_yoy = parse_number(row[4]) if len(row) > 4 else None

        status_str = str(row[5]).strip() if len(row) > 5 else ""
        is_provisional = "Προσωρινά" in status_str or "provisional" in status_str.lower()

        raw_observations.append({
            "year": year,
            "quarter": quarter,
            "period_date": period_date,
            "price_index": base_price_index,
            "base_qoq": base_qoq,
            "base_yoy": base_yoy,
            "is_provisional": is_provisional
        })

    # Sort chronologically to compute exact QoQ and YoY growth rates directly from index levels
    raw_observations.sort(key=lambda x: x["period_date"])

    observations = []
    for i, obs in enumerate(raw_observations):
        p_idx = obs["price_index"]
        
        # Calculate QoQ % directly from previous quarter index level
        if i >= 1:
            prev_idx = raw_observations[i - 1]["price_index"]
            qoq_pct = round(((p_idx - prev_idx) / prev_idx) * 100.0, 4) if prev_idx > 0 else None
        else:
            qoq_pct = obs["base_qoq"]

        # Calculate YoY % directly from index level 4 quarters ago
        if i >= 4:
            yoy_idx = raw_observations[i - 4]["price_index"]
            yoy_pct = round(((p_idx - yoy_idx) / yoy_idx) * 100.0, 4) if yoy_idx > 0 else None
        else:
            yoy_pct = obs["base_yoy"]

        observations.append({
            "area_name": GEOGRAPHICAL_REGIONS[0]["name"],
            "area_slug": GEOGRAPHICAL_REGIONS[0]["slug"],
            "year": obs["year"],
            "quarter": obs["quarter"],
            "period_date": obs["period_date"],
            "price_index": p_idx,
            "period_change_percent": qoq_pct,
            "annual_change_percent": yoy_pct,
            "is_provisional": obs["is_provisional"]
        })

    return observations, GEOGRAPHICAL_REGIONS

def load_datapackage_and_sync(db: Session):
    pkg_path = os.path.join(os.path.dirname(__file__), "datapackage.json")
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)

    # 1. Sync Data Source
    ds_id = pkg.get("extras", {}).get("identifier", "bank-of-greece-apt-index")
    data_source = db.query(DataSource).filter_by(id=ds_id).first()
    if not data_source:
        data_source = DataSource(
            id=ds_id,
            name=pkg.get("title", "Bank of Greece / Τράπεζα της Ελλάδος"),
            organization="Bank of Greece",
            dataset_name=pkg.get("title", "Δείκτης Τιμών Διαμερισμάτων κατά Γεωγραφική Περιοχή"),
            dataset_identifier=ds_id,
            dataset_url=pkg.get("extras", {}).get("uri", "https://opendata.bankofgreece.gr/en/dataset/5"),
            license=pkg.get("license", {}).get("title", "CC-BY-4.0"),
            description=pkg.get("description", "")
        )
        db.add(data_source)
        db.commit()

    # 2. Sync Resources
    resources_data = pkg.get("resources", [])
    synced_resources = []

    for res in resources_data:
        res_name = res.get("title") or f"{res['name']}.xls"
        res_url = res.get("path")
        
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", res_name)
        res_date = datetime.strptime(date_match.group(1), "%Y-%m-%d") if date_match else datetime.now()

        db_res = db.query(DatasetResource).filter_by(id=res["name"]).first()
        if not db_res:
            db_res = DatasetResource(
                id=res["name"],
                data_source_id=data_source.id,
                resource_name=res_name,
                resource_url=res_url,
                resource_description=res.get("description", res_name),
                resource_date=res_date,
                file_format=res.get("format", "XLS"),
                import_status="pending"
            )
            db.add(db_res)
            db.commit()

        synced_resources.append(db_res)

    return data_source, synced_resources

def import_single_resource(db: Session, resource: DatasetResource):
    import_log = ImportLog(
        dataset_resource_id=resource.id,
        status="processing",
        started_at=datetime.utcnow()
    )
    db.add(import_log)
    db.commit()

    try:
        file_path = download_or_get_local_file(resource.resource_url, resource.resource_name)
        observations, areas_found = parse_xls_file(file_path)

        created_count = 0
        updated_count = 0

        for area in areas_found:
            geo_area = db.query(GeographicalArea).filter_by(slug=area["slug"]).first()
            if not geo_area:
                geo_area = GeographicalArea(
                    name=area["name"],
                    slug=area["slug"],
                    area_type=area["type"],
                    source_code=area["code"]
                )
                db.add(geo_area)
                db.commit()

            area_obs = [o for o in observations if o["area_slug"] == area["slug"]]
            for obs in area_obs:
                existing = db.query(PriceIndex).filter_by(
                    geographical_area_id=geo_area.id,
                    period_date=obs["period_date"]
                ).first()

                if existing:
                    existing.dataset_resource_id = resource.id
                    existing.price_index = obs["price_index"]
                    existing.period_change_percent = obs["period_change_percent"]
                    existing.annual_change_percent = obs["annual_change_percent"]
                    existing.is_provisional = obs["is_provisional"]
                    updated_count += 1
                else:
                    new_idx = PriceIndex(
                        geographical_area_id=geo_area.id,
                        dataset_resource_id=resource.id,
                        period_date=obs["period_date"],
                        year=obs["year"],
                        quarter=obs["quarter"],
                        price_index=obs["price_index"],
                        period_change_percent=obs["period_change_percent"],
                        annual_change_percent=obs["annual_change_percent"],
                        is_provisional=obs["is_provisional"]
                    )
                    db.add(new_idx)
                    created_count += 1

        db.commit()

        import_log.status = "completed"
        import_log.completed_at = datetime.utcnow()
        import_log.records_created = created_count
        import_log.records_updated = updated_count
        resource.import_status = "completed"
        resource.imported_at = datetime.utcnow()
        db.commit()

        logger.info(f"Imported {resource.resource_name}: Created {created_count}, Updated {updated_count}")
        return True
    except Exception as e:
        db.rollback()
        import_log.status = "failed"
        import_log.completed_at = datetime.utcnow()
        import_log.error_message = str(e)
        resource.import_status = "failed"
        db.commit()
        logger.error(f"Failed to import {resource.resource_name}: {e}")
        return False

def import_all():
    db = SessionLocal()
    try:
        logger.info("Starting Python ETL Data Ingestion Pipeline...")
        data_source, resources = load_datapackage_and_sync(db)
        # Sort resources by resource_date ascending so latest release updates authoritative records last
        resources.sort(key=lambda r: r.resource_date)
        logger.info(f"Loaded metadata. Found {len(resources)} dataset resources.")

        success_count = 0
        for res in resources:
            if import_single_resource(db, res):
                success_count += 1

        logger.info(f"ETL Ingestion Finished. Successfully imported {success_count}/{len(resources)} resources.")
    finally:
        db.close()

if __name__ == "__main__":
    import_all()

