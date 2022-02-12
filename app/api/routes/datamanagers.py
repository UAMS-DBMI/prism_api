from fastapi import Depends, APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from asyncpg.exceptions import UniqueViolationError

router = APIRouter()

from .auth import logged_in_user, User

from ..util import Database


class DataManagerInfo(BaseModel):
    data_manager_id: int
    data_manager_name: str


async def get_data_manager_id_from_name(data_manager_name: str, db: Database):
    query = "select data_manager_id from data_manager where data_manager_name = $1"
    data_manager = await db.fetch_one(query, [data_manager_name])
    if len(data_manager) < 1:
        raise HTTPException(
            detail=f"Data_manager {data_manager_name}, not found. Ensure it exists in the data_manager manager.",
            status_code=422,
        )
    return data_manager["data_manager_id"]


@router.get("/", response_model=List[DataManagerInfo])
async def get_datamanagers(
    data_manager_name: str = None, db: Database = Depends()
) -> List[DataManagerInfo]:
    if data_manager_name:
        query = """
            select
                data_manager_id, data_manager_name
            from data_manager
            where
                data_manager_name = $1
        """
        return await db.fetch(query, [data_manager_name])

    query = """
        select
            data_manager_id, data_manager_name
        from data_manager
    """
    return await db.fetch(query)


@router.post("/")
async def create_datamanager(
    data_manager_name: str,
    db: Database = Depends(),
):
    query = """
        insert into data_manager
        (data_manager_name)
        values
        ($1)
        returning data_manager_id
    """
    try:
        data_manager = await db.fetch_one(query, [data_manager_name])
        if len(data_manager) < 1:
            raise HTTPException(
                detail=f"Failed to create data manager", status_code=422
            )
        return data_manager["data_manager_id"]
    except UniqueViolationError:
        raise HTTPException(
            detail=f'Failed to create data_manager, data_manager_name must be unique and "{data_manager_name}" already exists.',
            status_code=422,
        )
