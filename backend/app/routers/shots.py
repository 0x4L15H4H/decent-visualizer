import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.db import get_supabase
from app.models.shot import ShotSummary, ShotUpload, ShotUploadCreate, ShotUploadUpdate
from app.storage.shots import ShotStorage

router = APIRouter(prefix="/shots", tags=["shots"])


def _storage() -> ShotStorage:
    return ShotStorage(get_supabase())


@router.get("", response_model=list[ShotSummary])
def list_shots(storage: ShotStorage = Depends(_storage)):
    return storage.list()


@router.get("/{shot_id}", response_model=ShotUpload)
def get_shot(shot_id: str, storage: ShotStorage = Depends(_storage)):
    shot = storage.get(shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@router.post("", response_model=ShotUpload, status_code=201)
def create_shot(data: ShotUploadCreate, storage: ShotStorage = Depends(_storage)):
    shot_id = str(uuid.uuid4())
    return storage.create(shot_id, data)


@router.patch("/{shot_id}", response_model=ShotUpload)
def update_shot(shot_id: str, data: ShotUploadUpdate, storage: ShotStorage = Depends(_storage)):
    shot = storage.update(shot_id, data)
    if shot is None:
        raise HTTPException(status_code=404, detail="Shot not found")
    return shot


@router.delete("/{shot_id}", status_code=204)
def delete_shot(shot_id: str, storage: ShotStorage = Depends(_storage)):
    if not storage.delete(shot_id):
        raise HTTPException(status_code=404, detail="Shot not found")
