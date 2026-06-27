from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EntityKind = Literal["roaster", "producer", "farm", "variety", "process"]
NormalizationKind = Literal["roaster", "producer", "farm", "country", "variety", "process"]
AliasSource = Literal["user", "llm", "import", "system"]


class EntityAlias(BaseModel):
    id: str
    entity_id: str
    alias: str
    source: AliasSource
    created_at: datetime


class CanonicalEntity(BaseModel):
    id: str
    kind: EntityKind
    name: str
    country_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    aliases: list[EntityAlias] = Field(default_factory=list)


class EntityCreate(BaseModel):
    kind: EntityKind
    name: str
    country_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    name: str | None = None
    country_code: str | None = None
    metadata: dict[str, Any] | None = None


class EntityAliasCreate(BaseModel):
    alias: str
    source: AliasSource = "user"


class NormalizationCandidate(BaseModel):
    id: str
    kind: NormalizationKind
    canonical_name: str
    aliases: list[str]
    score: float
    match_reason: str
