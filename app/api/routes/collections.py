from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from asyncpg.exceptions import UniqueViolationError
import re

router = APIRouter()

from .auth import logged_in_user, User

from ..util import Database


class CollectionInfo(BaseModel):
    collection_id: int
    collection_slug: str
    collection_name: str
    collection_doi: str


async def get_collection_id_from_slug(collection_slug: str, db: Database):
    query = "select collection_id from collection where collection_slug = $1"
    collection = await db.fetch_one(query, [collection_slug])
    if len(collection) < 1:
        raise HTTPException(
            detail=f"Invalid collection slug: {collection_slug}", status_code=422
        )
    return collection["collection_id"]


@router.get("/", response_model=List[CollectionInfo])
async def get_all_collections(
    collection_slug: str = None, db: Database = Depends()
) -> List[CollectionInfo]:
    async def get_collections_by_slug(site_name):
        query = """
            select
                collection_id, collection_slug,
                collection_name, collection_doi
            from collection
            where collection_id = $1
            group by collection_id
        """

        return await db.fetch(query, [collection_slug])

    query = """
        select
            collection_id, collection_slug,
            collection_name, collection_doi
        from collection
        group by collection_id
    """

    if collection_slug is not None:
        return await get_collections_by_slug(collection)

    return await db.fetch(query)


@router.get("/{collection_slug}/{version_id}", response_model=CollectionInfo)
async def get_collection_version_info(
    collection_slug: str, version_id: int, db: Database = Depends()
) -> CollectionInfo:
    query = """
        select
            collection_id, collection_slug,
            collection_name, collection_doi
        from collection
        natural join version
        where collection_id = $1
          and version_id = $2
        group by collection_id
    """

    return await db.fetch_one(query, [collection_slug, version_id])


@router.get("/{collection_slug}", response_model=CollectionInfo)
async def get_collection_info(
    collection_slug: str, db: Database = Depends()
) -> CollectionInfo:
    query = """
        select
            collection_id, collection_slug,
            collection_name, collection_doi
        from collection
        natural join version
        where collection_id = $1
        group by collection_id
    """

    return await db.fetch_one(query, [collection_slug])


@router.post("/")
async def create_collection(
    collection_slug: str,
    collection_name: str,
    collection_doi: str,
    db: Database = Depends(),
):
    slug_re = re.compile(r"[-_a-zA-Z0-9]+")
    if re.fullmatch(slug_re, collection_slug) == None:
        raise HTTPException(
            detail=f'"{collection_slug}" is not a valid collection slug. It must conform to the regular expression /[-_a-zA-Z0-9]+/ which is letters, numers, dashes, and underscores only.',
            status_code=422,
        )
    query = """
        insert into collection
        (collection_name, collection_doi, collection_slug)
        values
        ($1, $2, $3)
        returning collection_id
    """
    try:
        collection = await db.fetch_one(
            query, [collection_name, collection_doi, collection_slug]
        )
        if len(collection) < 1:
            raise HTTPException(detail=f"Failed to create collection", status_code=422)
        collection_id = collection["collection_id"]
        query = """
            insert into version
            (collection_id)
            values
            ($1)
        """
        await db.fetch(query, [collection_id])
        return collection_id
    except UniqueViolationError:
        raise HTTPException(
            detail=f'Failed to create collection, collection_slug must be unique and "{collection_slug}" already exists.',
            status_code=422,
        )
