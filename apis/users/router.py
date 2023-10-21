from apis.auth.controller import AuthController
from apis.users.controller import UserController
from apis.users.models import User
from fastapi import APIRouter, Request

# Router
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Define Controller
user_controller = UserController()
auth_controller = AuthController()

@router.get("/{id}", response_model=User)
async def get(id: str):
    return await user_controller.get_item(id)

@router.get("", response_model=list[User])
async def get_items(request: Request):
    current_user = auth_controller.get_user_from_session(request)
    return await user_controller.get_users(exclude_user=current_user)

@router.on_event("startup")
async def startup():
    await user_controller.seed()
