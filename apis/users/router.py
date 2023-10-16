from apis.users.controller import UserController
from apis.users.models import User
from fastapi import APIRouter

# Router
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Define Controller
controller = UserController()

@router.get("/{id}", response_model=User)
async def get(id: str):
    return await controller.get_item(id)

@router.get("", response_model=list[User])
async def get_items():
    return await controller.get_items()

@router.on_event("startup")
async def startup():
    await controller.seed()
