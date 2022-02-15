from fastapi import Depends, APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import requests

router = APIRouter()

from .auth import logged_in_user, User
from .collections import get_collection_id_from_slug
from .datamanagers import get_data_manager_id_from_name
from .versions import get_latest_version, add_file_to_version
from .filetypes import get_or_create_file_type

from ..util import Database

security = HTTPBasic()

class FileInfo(BaseModel):
    file_id: int
    data_manager_id: int
    mime_type: str
    external_id: str
    data_manager_name: str
    file_type_group_name: Optional[str] = None

class FileUpload(BaseModel):
    collection_slug: str
    data_manager_name: str
    external_id: str
    mime: str

class PathDBImage(BaseModel):
    image_id: str
    subject_id: str
    study_id: str
    external_id: str

@router.get("/sync/pathdb/{collection_slug}", response_model=List[PathDBImage])
def sync_pathdb(collection_slug: str, request: Request, credentials: HTTPBasicCredentials = Depends(security)) -> List[PathDBImage]:
    auth = request.headers['Authorization']
    url = "http://quip-pathdb-pathdb.apps.dbmi.cloud/listofimages"
    querystring = { "_format":"json" }
    headers = { "Authorization": auth }
    response = requests.request("GET", url, headers=headers, params=querystring)
    ret = []
    for row in response.json():
        nid = row['nid'][0]['value']
        subject_id = row['clinicaltrialsubjectid'][0]['value']
        image_id = row['imageid'][0]['value']
        study_id = row['studyid'][0]['value']
        ret.append(PathDBImage(image_id = image_id, subject_id = subject_id, study_id = study_id, external_id = f'http://quip-pathdb-pathdb.apps.dbmi.cloud/caMicroscope/apps/viewer/viewer.html?slideId={nid}&mode=pathdb'))
    return ret


@router.post("/import")
async def import_file(
    upload: FileUpload,
    db: Database = Depends(),
):
    collection_id = await get_collection_id_from_slug(upload.collection_slug, db)
    version_id = await get_latest_version(collection_id, upload.collection_slug, db)
    data_manager_id = await get_data_manager_id_from_name(upload.data_manager_name, db)
    file_type_id = await get_or_create_file_type(upload.mime, db)
    query = """
		insert into file
		(data_manager_id, file_type_id, external_id)
		values
		($1, $2, $3)
		returning file_id
	"""
    file = await db.fetch_one(query, [data_manager_id, file_type_id, upload.external_id])
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
            and version.version_id = $2
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
