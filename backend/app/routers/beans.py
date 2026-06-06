from fastapi import APIRouter, Depends, HTTPException

from app.db import get_supabase
from app.models.bean import Bean, BeanCreate, BeanUpdate
from app.storage.beans import BeanStorage

router = APIRouter(prefix="/beans", tags=["beans"])


def _storage() -> BeanStorage:
    return BeanStorage(get_supabase())


@router.get("/", response_model=list[Bean])
def list_beans(storage: BeanStorage = Depends(_storage)):
    return storage.list()


@router.get("/{bean_id}", response_model=Bean)
def get_bean(bean_id: str, storage: BeanStorage = Depends(_storage)):
    bean = storage.get(bean_id)
    if bean is None:
        raise HTTPException(status_code=404, detail="Bean not found")
    return bean


@router.post("/", response_model=Bean, status_code=201)
def create_bean(data: BeanCreate, storage: BeanStorage = Depends(_storage)):
    return storage.create(data)


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
