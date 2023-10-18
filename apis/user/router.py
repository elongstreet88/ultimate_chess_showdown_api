from apis.auth.controller import AuthController
from apis.users.controller import UserController
from apis.users.models import User
from fastapi import APIRouter, Depends

# Router
router = APIRouter(
    prefix="/user",
    tags=["User"]
)

# Define Controller
controller = UserController()
auth_controller = AuthController()

# Auth
auth = auth_controller.ensure_authenticated

@router.get("", response_model=User)
async def get(user = Depends(auth)):
    return user

@router.on_event("startup")
async def startup():
    await controller.seed()
