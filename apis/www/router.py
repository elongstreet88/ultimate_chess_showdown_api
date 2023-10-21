from pathlib import Path
from tools.routers.static_files_router import static_files_router

router = static_files_router(
    root_directory=Path(__file__).parent / "static",
    prefix="/app",
    tags=["App"]
)
