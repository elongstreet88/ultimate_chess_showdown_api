from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse

# Constants
CACHE_DURATION = 300  # 5 minutes

class StaticFilesController:
    def __init__(self, root_directory: str):
        self.root_path = Path(root_directory).resolve()

    async def serve_path(self, path: str):
        served_path = (self.root_path / path).resolve()

        # Ensure path is secure
        if ".." in path or "//" in path or (self.root_path not in served_path.parents and served_path != self.root_path):
            raise HTTPException(status_code=404, detail="Not Found")

        # Serve index.html if path is a directory
        if served_path.is_dir():
            served_path = served_path / "index.html"

        # Return 404 if file doesn't exist
        if not served_path.exists():
            raise HTTPException(status_code=404, detail="Not Found")

        # Serve the file with caching
        response = FileResponse(served_path)
        response.headers["Cache-Control"] = f"public, max-age={CACHE_DURATION}"
        return response
