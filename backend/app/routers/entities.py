from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db import get_supabase
from app.dependencies import get_current_user
from app.lib.countries import CountryCandidate, country_candidates
from app.models.entities import (
    CanonicalEntity,
    EntityAlias,
    EntityAliasCreate,
    EntityCreate,
    EntityKind,
    EntityUpdate,
    NormalizationCandidate,
)
from app.storage.entities import EntityStorage

router = APIRouter(
    prefix="/entities",
    tags=["entities"],
    dependencies=[Depends(get_current_user)],
)
normalization_router = APIRouter(
    prefix="/normalization",
    tags=["normalization"],
    dependencies=[Depends(get_current_user)],
)


def _storage() -> EntityStorage:
    return EntityStorage(get_supabase())


@router.get("", response_model=list[CanonicalEntity])
def list_entities(
    kind: EntityKind | None = None,
    q: str | None = None,
    storage: EntityStorage = Depends(_storage),
):
    return storage.list_entities(kind=kind, q=q)


@router.post("", response_model=CanonicalEntity, status_code=201)
def create_entity(data: EntityCreate, storage: EntityStorage = Depends(_storage)):
    return storage.create(data)


@router.get("/{entity_id}", response_model=CanonicalEntity)
def get_entity(entity_id: str, storage: EntityStorage = Depends(_storage)):
    entity = storage.get(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}", response_model=CanonicalEntity)
def update_entity(
    entity_id: str,
    data: EntityUpdate,
    storage: EntityStorage = Depends(_storage),
):
    entity = storage.update(entity_id, data)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/{entity_id}/aliases", response_model=EntityAlias, status_code=201)
def add_entity_alias(
    entity_id: str,
    data: EntityAliasCreate,
    storage: EntityStorage = Depends(_storage),
):
    alias = storage.add_alias(entity_id=entity_id, alias=data.alias, source=data.source)
    if alias is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return alias


@router.delete("/{entity_id}/aliases/{alias_id}", status_code=204)
def delete_entity_alias(
    entity_id: str,
    alias_id: str,
    storage: EntityStorage = Depends(_storage),
):
    if not storage.delete_alias(entity_id=entity_id, alias_id=alias_id):
        raise HTTPException(status_code=404, detail="Alias not found")


@normalization_router.get("/candidates", response_model=list[NormalizationCandidate])
def find_normalization_candidates(
    kind: EntityKind,
    q: Annotated[str, Query(min_length=1)],
    storage: EntityStorage = Depends(_storage),
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
):
    return storage.candidates(kind=kind, value=q, limit=limit)


@normalization_router.get("/countries", response_model=list[CountryCandidate])
def find_country_candidates(
    q: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
):
    return country_candidates(q, limit=limit)
