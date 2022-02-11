from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

from .auth import logged_in_user, User

from ..util import Database


class FileInfo(BaseModel):
    file_id: int
    data_manager_id: int
    mime_type: str
    external_id: str
    data_manager_name: str
    group_name: Optional[str] = None


# add a file POST
# - collection_slug/id
# - data_manager_id
# - version_id
# - external_id
# - mime
@router.post("/import")
async def import_file(
    collection_slug: str,
    data_manager_id: int,
    external_id: str,
    mime: str,
    db: Database = Depends(),
):
    # get mime type id
    # create if doesn't exist
    # add file to list and most recent version of collection
    pass


# GET file types
# all
@router.get("/{collection_slug}/{version_id}")
async def get_all_files(
    collection_slug: str, version_id: int, db: Database = Depends()
) -> List[FileInfo]:
    query = """
        select
            file_id, data_manager_id,
            mime_type, external_id,
            data_manager_name, group_name
        from version
        natural join version_file
        natural join file
        natural join collection
        natural join data_manager
        natural join file_type
        natural join file_type_group
        where collection_slug = $1
          and version_id = $2
    """

    return await db.fetch_one(query, [collection_slug, version_id])


# GET a file
# - by id
@router.get("/{file_id}")
async def get_file(file_id: int, db: Database = Depends()) -> FileInfo:
    query = """
        select
            file_id, data_manager_id,
            mime_type, external_id,
            data_manager_name, group_name
        from file
        natural join data_manager
        natural join file_type
        natural join file_type_group
        where file_id = $1
    """

    return await db.fetch_one(query, [file_id])
