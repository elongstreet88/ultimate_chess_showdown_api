from fastapi import APIRouter, FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

class APIDocs(APIRouter):
    """
    This class is the default "/" router, all home routes are defined here.
    This uses a class version of the APIRouter to allow it to access the FastAPI app object.
    """

    def __init__(self, app: FastAPI):
        super().__init__(
            prefix="",
            tags=["Default"]
        )
        self.app = app

        @self.get(f"/docs", include_in_schema=False)
        async def custom_swagger_ui_html(request: Request):
            """
            Return Swagger UI documentation.
            This is required to have docs live under the api root path.
            Note - This parses and rewrites the swagger html to change the url to the correct path.
            See: https://github.com/tiangolo/fastapi/issues/4211#issuecomment-983600161
            """
            root_path = request.scope.get("root_path", "").rstrip("/")
            openapi_url = root_path + app.openapi_url
            return get_swagger_ui_html(
                openapi_url = openapi_url,
                title       = app.title,
            )

        @self.get(f"/openapi.json", include_in_schema=False)
        async def openapi():
            """
            Return OpenAPI documentation.
            This is required to have docs live under the api root path.
            """
            return get_openapi(
                title       = app.title, 
                version     = app.version, 
                routes      = app.routes,
                description = app.description,
            )