from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.config import get_settings
from app.db import get_supabase
from app.dependencies import get_current_user
from app.lib.photo_extract import get_bean_info_from_image
from app.models.bean import Bean, BeanCreate, BeanExtracted, BeanUpdate
from app.storage.beans import BeanStorage

router = APIRouter(prefix="/beans", tags=["beans"], dependencies=[Depends(get_current_user)])

_MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _storage() -> BeanStorage:
    return BeanStorage(get_supabase())


@router.get("", response_model=list[Bean])
def list_beans(storage: BeanStorage = Depends(_storage)):
    return storage.list()


@router.get("/photo-extract/enabled")
def photo_extract_enabled():
    settings = get_settings()
    return {
        "enabled": settings.gemini_api_key is not None and settings.parallel_api_key is not None
    }


@router.get("/{bean_id}", response_model=Bean)
def get_bean(bean_id: str, storage: BeanStorage = Depends(_storage)):
    bean = storage.get(bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    return bean


@router.post("", response_model=Bean, status_code=201)
def create_bean(data: BeanCreate, storage: BeanStorage = Depends(_storage)):
    return storage.create(data)


@router.post("/photo-extract/upload", response_model=BeanExtracted)
async def extract_from_photo(file: UploadFile):
    settings = get_settings()
    if not settings.gemini_api_key or not settings.parallel_api_key:
        raise HTTPException(status_code=503, detail="Photo extraction not configured")

    image_bytes = await file.read()
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")

    result = await get_bean_info_from_image(
        gemini_api_key=settings.gemini_api_key,
        parallel_api_key=settings.parallel_api_key,
        image_bytes=image_bytes,
        mime_type=file.content_type or "image/jpeg",
    )
    if not result:
        raise HTTPException(status_code=422, detail="Could not extract bean info from image")
    return result


@router.patch("/{bean_id}", response_model=Bean)
def update_bean(bean_id: str, data: BeanUpdate, storage: BeanStorage = Depends(_storage)):
    bean = storage.update(bean_id, data)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    return bean


@router.delete("/{bean_id}", status_code=204)
def delete_bean(bean_id: str, storage: BeanStorage = Depends(_storage)):
    if not storage.delete(bean_id):
        raise HTTPException(status_code=404, detail="Bean not found")
