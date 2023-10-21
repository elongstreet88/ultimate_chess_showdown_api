from fastapi import APIRouter
from tools.controller.static_files_controller import StaticFilesController

def static_files_router(root_directory: str, prefix: str, tags: list):
    router = APIRouter(
        prefix=prefix,
        tags=tags
    )
    controller = StaticFilesController(root_directory=root_directory)

    @router.get("/{path:path}")
    async def catch_all(path: str = ""):
        return await controller.serve_path(path)

    return router
