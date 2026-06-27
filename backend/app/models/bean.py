from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class EntityReference(BaseModel):
    id: str
    name: str


class CountryReference(BaseModel):
    code: str
    name: str


class Bean(BaseModel):
    id: str
    name: str
    roaster: EntityReference
    producer: EntityReference | None = None
    farm: EntityReference | None = None
    country: CountryReference | None = None
    variety: EntityReference | None = None
    process: EntityReference | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None
    created_at: datetime


class BeanCreate(BaseModel):
    name: str
    roaster_id: str
    producer_id: str | None = None
    farm_id: str | None = None
    country_code: str | None = None
    variety_id: str | None = None
    process_id: str | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None


class CanonicalSelection(BaseModel):
    resolution: Literal["matched", "proposed"]
    canonical_id: str | None = None
    name: str


class BeanExtracted(BaseModel):
    name: str | None = None
    roaster: CanonicalSelection | None = None
    producer: CanonicalSelection | None = None
    farm: CanonicalSelection | None = None
    country: CanonicalSelection | None = None
    variety: CanonicalSelection | None = None
    process: CanonicalSelection | None = None
    notes: str | None = None


class BeanUpdate(BaseModel):
    name: str | None = None
    roaster_id: str | None = None
    producer_id: str | None = None
    farm_id: str | None = None
    country_code: str | None = None
    variety_id: str | None = None
    process_id: str | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None
