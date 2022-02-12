from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError

router = APIRouter()

from .auth import logged_in_user, User
from .collections import get_collection_id_from_slug

from ..util import Database


class VersionInfo(BaseModel):
    version_id: int
    collection_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    created_on: datetime


async def get_latest_version(collection_id: id, collection_slug: str, db: Database):
    query = "select max(version_id) as version_id from version where collection_id = $1"
    version = await db.fetch_one(query, [collection_id])
    if len(version) < 1:
        raise HTTPException(
            detail=f"No version exists for collection: {collection_slug}",
            status_code=422,
        )
    return version["version_id"]


@router.get("/{collection_slug}", response_model=List[VersionInfo])
async def get_filetypes(
    collection_slug: str, db: Database = Depends()
) -> List[VersionInfo]:
    query = """
        select
           version_id, collection_id, name, description, created_on 
        from version
        natural join collection
        where collection_slug = $1
    """
    return await db.fetch(query, [collection_slug])


@router.post("/{collection_slug}")
async def create_version(
    collection_slug: str,
    name: str = None,
    description: str = None,
    db: Database = Depends(),
):
    collection_id = await get_collection_id_from_slug(collection_slug, db)
    query = """
        insert into version
        (collection_id, name, description)
        values
        ($1, $2, $3)
        returning version_id
    """
    version = await db.fetch_one(query, [collection_id, name, description])
    return version["version_id"]


@router.post("/{version_id}/{file_id}")
async def add_file_to_version(
    file_id: int,
    version_id: int,
    db: Database = Depends(),
):
    query = """
        insert into version_file
        (version_id, file_id)
        values
        ($1, $2)
    """
    try:
        await db.fetch_one(query, [version_id, file_id])
    except ForeignKeyViolationError as e:
        raise HTTPException(
            detail=f"Failed to add file to version. {e.detail}",
            status_code=422,
        )
