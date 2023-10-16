from fastapi import APIRouter
from apis.app.controller import AppController

# Router
router = APIRouter(
    prefix="/app",
    tags=["App"]
)

# Controller
controller = AppController()

@router.get("/{path:path}")
async def catch_all(path: str = ""):
    result = await controller.serve_path(path)
    return result