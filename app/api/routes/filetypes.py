from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError

router = APIRouter()

from .auth import logged_in_user, User

from ..util import Database


class FileTypeInfo(BaseModel):
    file_type_id: int
    file_type_group_name: Optional[str] = None
    mime_type: str


class FileTypeGroupInfo(BaseModel):
    file_type_group_id: int
    file_type_group_name: str


@router.get("/", response_model=List[FileTypeInfo])
async def get_filetypes(
    mime_type: str = None, db: Database = Depends()
) -> List[FileTypeInfo]:
    if mime_type:
        query = """
            select
                file_type_id, file_type_group_name, mime_type
            from file_type
            left join file_type_group
                on file_type.file_type_group_id = file_type_group.file_type_group_id
            where
                mime_type = $1
        """
        return await db.fetch(query, [mime_type])

    query = """
        select
            file_type_id, file_type_group_name, mime_type
        from file_type
        left join file_type_group
            on file_type.file_type_group_id = file_type_group.file_type_group_id
    """
    return await db.fetch(query)


@router.get("/groups", response_model=List[FileTypeGroupInfo])
async def get_filetype_groups(
    group_name: str = None, db: Database = Depends()
) -> List[FileTypeGroupInfo]:
    if group_name:
        query = """
            select
                file_type_group_id, file_type_group_name
            from file_type_group
            where
                file_type_group_name = $1
        """
        group = await db.fetch_one(query, [group_name])
        if len(group) < 1:
            raise HTTPException(detail=f'No group by name "{group_name}" exists.')
        return [group]

    query = """
        select
            file_type_group_id, file_type_group_name
        from file_type_group
    """
    return await db.fetch(query)


@router.post("/groups")
async def create_filetype_group(
    group_name: str,
    db: Database = Depends(),
):
    query = """
        insert into file_type_group
        (file_type_group_name)
        values
        ($1)
        returning file_type_group_id
    """
    try:
        data_manager = await db.fetch_one(query, [group_name])
        if len(data_manager) < 1:
            raise HTTPException(detail=f"Failed to create file group", status_code=422)
        return data_manager["file_type_group_id"]
    except UniqueViolationError:
        raise HTTPException(
            detail=f'Failed to create file group, group names must be unique and "{group_name}" already exists.',
            status_code=422,
        )


@router.post("/group/{file_type_id}/{file_type_group_id}")
async def add_filetype_to_group(
    file_type_id: int,
    file_type_group_id: int,
    db: Database = Depends(),
):
    query = """
        update file_type
        set file_type_group_id = $2
        where file_type_id = $1
    """
    try:
        await db.fetch_one(query, [file_type_id, file_type_group_id])
    except ForeignKeyViolationError as e:
        raise HTTPException(
            detail=f"Failed to add file_type to file_type_group. {e.detail}",
            status_code=422,
        )
