import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    organization = Column(String, nullable=False)
    dataset_name = Column(String, nullable=False)
    dataset_identifier = Column(String, nullable=False)
    dataset_url = Column(String, nullable=False)
    license = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resources = relationship("DatasetResource", back_populates="data_source", cascade="all, delete-orphan")

class DatasetResource(Base):
    __tablename__ = "dataset_resources"

    id = Column(String, primary_key=True, default=generate_uuid)
    data_source_id = Column(String, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False)
    resource_name = Column(String, nullable=False)
    resource_url = Column(String, nullable=False)
    resource_description = Column(Text, nullable=True)
    resource_date = Column(DateTime, nullable=False)
    file_format = Column(String, default="XLS")
    imported_at = Column(DateTime, nullable=True)
    checksum = Column(String, nullable=True)
    import_status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    data_source = relationship("DataSource", back_populates="resources")
    price_indices = relationship("PriceIndex", back_populates="dataset_resource", cascade="all, delete-orphan")
    imports = relationship("ImportLog", back_populates="dataset_resource", cascade="all, delete-orphan")

class GeographicalArea(Base):
    __tablename__ = "geographical_areas"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    parent_id = Column(String, ForeignKey("geographical_areas.id"), nullable=True)
    area_type = Column(String, nullable=False)  # country, city, region
    source_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("GeographicalArea", remote_side=[id], backref="children")
    price_indices = relationship("PriceIndex", back_populates="geographical_area", cascade="all, delete-orphan")

class PriceIndex(Base):
    __tablename__ = "price_indices"

    id = Column(String, primary_key=True, default=generate_uuid)
    geographical_area_id = Column(String, ForeignKey("geographical_areas.id", ondelete="CASCADE"), nullable=False)
    dataset_resource_id = Column(String, ForeignKey("dataset_resources.id", ondelete="CASCADE"), nullable=False)
    period_date = Column(DateTime, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    price_index = Column(Float, nullable=False)
    period_change_percent = Column(Float, nullable=True)
    annual_change_percent = Column(Float, nullable=True)
    is_provisional = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    geographical_area = relationship("GeographicalArea", back_populates="price_indices")
    dataset_resource = relationship("DatasetResource", back_populates="price_indices")

    __table_args__ = (
        UniqueConstraint("geographical_area_id", "period_date", "dataset_resource_id", name="uq_area_date_resource"),
        Index("idx_price_indices_area", "geographical_area_id"),
        Index("idx_price_indices_period_date", "period_date"),
        Index("idx_price_indices_year", "year"),
        Index("idx_price_indices_resource", "dataset_resource_id"),
    )

class ImportLog(Base):
    __tablename__ = "imports"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_resource_id = Column(String, ForeignKey("dataset_resources.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)  # pending, processing, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset_resource = relationship("DatasetResource", back_populates="imports")
