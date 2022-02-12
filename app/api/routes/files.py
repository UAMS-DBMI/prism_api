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
    data_manager_name: str,
    external_id: str,
    mime: str,
    db: Database = Depends(),
):
    query = "select collection_id from collection where collection_slug = $1"
    collection = await db.fetch_one(query, [collection_slug])
    if len(collection) < 1:
        raise HTTPException(
            detail=f"Invalid collection slug: {collection_slug}", status_code=422
        )
    collection_id = collection["collection_id"]
    query = "select max(version_id) as version_id from version where collection_id = $1"
    version = await db.fetch_one(query, [collection_id])
    if len(version) < 1:
        raise HTTPException(
            detail=f"No version exists for collection: {collection_slug}",
            status_code=422,
        )
    version_id = version["version_id"]
    query = "select data_manager_id from data_manager where data_manager_name = $1"
    data_manager = await db.fetch_one(query, [data_manager_name])
    if len(data_manager) < 1:
        raise HTTPException(
            detail=f"Data_manager {data_manager_name}, not found. Ensure it exists in the data_manager manager.",
            status_code=422,
        )
    data_manager_id = data_manager["data_manager_id"]
    query = "select file_type_id from file_type where mime_type = $1"
    file_type = await db.fetch_one(query, [mime])
    if len(file_type) < 1:
        query = """
    		insert into file_type
    		(mime_type)
    		values
    		($1)
    		returning file_type_id
    	"""
        file_type = await db.fetch_one(query, [mime])
    file_type_id = file_type["file_type_id"]
    query = """
		insert into file
		(data_manager_id, file_type_id, external_id)
		values
		($1, $2, $3)
		returning file_id
	"""
    file = await db.fetch_one(query, [data_manager_id, file_type_id, external_id])
    file_id = file["file_id"]
    query = """
		insert into version_file
		(version_id, file_id)
		values
		($1, $2)
	"""
    await db.fetch(query, [version_id, file_id])
    return file_id


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
