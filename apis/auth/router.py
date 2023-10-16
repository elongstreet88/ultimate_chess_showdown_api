from fastapi import Request
from fastapi.responses import RedirectResponse
from apis.auth.controller import AuthController
from tools.config.app_settings import app_settings
from google_auth_oauthlib.flow import Flow
from fastapi import Depends
from starlette.responses import RedirectResponse
from fastapi import APIRouter

# Router
router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# Controller
controller = AuthController()
auth = controller.ensure_authenticated

@router.get("")
async def login(request: Request, next: str = "/"):
    result = await controller.login(request, next)
    return result

@router.get('/callback')
async def auth_callback(request: Request, state: str = "/"):
    result = await controller.auth_callback(request, state)
    return result

@router.get('/logout')
async def logout(request: Request):
    return await controller.logout(request)

@router.get("/test", response_model=None)
async def test_route(current_user = Depends(auth)):
    return {"message": "You're logged in!", "user": current_user}