from fastapi import FastAPI, APIRouter

from api.util import db
from api.routes import auth
from api.routes import collections
from api.routes import files

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    print(20 * "#", "database connecting")
    await db.setup(database="collection_manager")
    print(20 * "#", "database connected")


router_v1 = APIRouter()
router_v1.include_router(collections.router, prefix="/collections")
router_v1.include_router(files.router, prefix="/files")

app.include_router(auth.router)
app.include_router(router_v1, prefix="/v1")
