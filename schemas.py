from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class GeographicalAreaSchema(BaseModel):
    id: str
    name: str
    slug: str
    area_type: str
    source_code: Optional[str] = None

    class Config:
        from_attributes = True

class PriceIndexSchema(BaseModel):
    id: str
    geographical_area_id: str
    area_name: Optional[str] = None
    area_slug: Optional[str] = None
    period_date: datetime
    year: int
    quarter: int
    price_index: float
    period_change_percent: Optional[float] = None
    annual_change_percent: Optional[float] = None
    is_provisional: bool = False
    resource_name: Optional[str] = None

    class Config:
        from_attributes = True

class SummaryMetricsSchema(BaseModel):
    latest_index: float
    latest_quarter: str
    latest_year: int
    qoq_change: Optional[float] = None
    yoy_change: Optional[float] = None
    cumulative_change: float
    market_direction: str
    is_provisional: bool
    last_updated_date: Optional[datetime] = None
    resource_name: Optional[str] = None
    total_observations: int
    first_period: str

class DatasetResourceSchema(BaseModel):
    id: str
    resource_name: str
    resource_url: str
    resource_date: datetime
    file_format: str
    import_status: str
    imported_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DataSourceSchema(BaseModel):
    id: str
    name: str
    organization: str
    dataset_name: str
    dataset_identifier: str
    dataset_url: str
    license: str
    description: str
    resources: List[DatasetResourceSchema] = []

    class Config:
        from_attributes = True
