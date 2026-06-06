from datetime import datetime

from pydantic import BaseModel


class Bean(BaseModel):
    id: str
    name: str
    roaster: str
    farmer: str | None = None
    origin: str | None = None
    variety: str | None = None
    process: str | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None


class BeanCreate(BaseModel):
    name: str
    roaster: str
    farmer: str | None = None
    origin: str | None = None
    variety: str | None = None
    process: str | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None


class BeanUpdate(BaseModel):
    name: str | None = None
    roaster: str | None = None
    farmer: str | None = None
    origin: str | None = None
    variety: str | None = None
    process: str | None = None
    roast_level: str | None = None
    roast_date: datetime | None = None
    notes: str | None = None
