from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

from .auth import logged_in_user, User

from ..util import Database


class CollectionInfo(BaseModel):
    collection_id: int
    collection_slug: str
    collection_name: str
    collection_doi: str


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


@router.get("/{collection_slug}/{version_id}")
async def get_collection_info(
    collection_slug: str, version_id: int, db: Database = Depends()
):
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
