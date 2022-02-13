from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

from .auth import logged_in_user, User
from .collections import get_collection_id_from_slug
from .datamanagers import get_data_manager_id_from_name
from .versions import get_latest_version, add_file_to_version
from .filetypes import get_or_create_file_type

from ..util import Database


class FileInfo(BaseModel):
    file_id: int
    data_manager_id: int
    mime_type: str
    external_id: str
    data_manager_name: str
    file_type_group_name: Optional[str] = None


@router.post("/import")
async def import_file(
    collection_slug: str,
    data_manager_name: str,
    external_id: str,
    mime: str,
    db: Database = Depends(),
):
    collection_id = await get_collection_id_from_slug(collection_slug, db)
    version_id = await get_latest_version(collection_id, collection_slug, db)
    data_manager_id = await get_data_manager_id_from_name(data_manager_name, db)
    file_type_id = await get_or_create_file_type(mime, db)
    query = """
		insert into file
		(data_manager_id, file_type_id, external_id)
		values
		($1, $2, $3)
		returning file_id
	"""
    file = await db.fetch_one(query, [data_manager_id, file_type_id, external_id])
    file_id = file["file_id"]
    await add_file_to_version(file_id, version_id, db)
    return file_id


@router.get("/{collection_slug}/{version_id}", response_model=List[FileInfo])
async def get_all_files(
    collection_slug: str, version_id: int, db: Database = Depends()
) -> List[FileInfo]:
    query = """
        select
            file_id, data_manager_id,
            mime_type, external_id,
            data_manager_name, file_type_group_name
        from version
        natural join version_file
        natural join file
        natural join collection
        natural join data_manager
        natural join file_type
        left join file_type_group
            on file_type.file_type_id = file_type_group.file_type_id
        where collection_slug = $1
            and version_id = $2
    """

    return await db.fetch(query, [collection_slug, version_id])


@router.get("/{file_id}", response_model=FileInfo)
async def get_file(file_id: int, db: Database = Depends()) -> FileInfo:
    query = """
        select
            file_id, data_manager_id,
            mime_type, external_id,
            data_manager_name, file_type_group_name
        from file
        natural join data_manager
        natural join file_type
        left join file_type_group
        	on file_type.file_type_group_id = file_type_group.file_type_group_id
        where file_id = $1
    """

    return await db.fetch_one(query, [file_id])
