from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from requests import session
from apis.auth.controller import AuthController
from apis.games.controller import GameController
from apis.games.models import ChessAction, Game
from apis.users.controller import UserController

# Router
router = APIRouter(
    prefix="/games",
    tags=["Games"]
)

# Define Controller
controller = GameController()
auth_controller = AuthController()
user_controller = UserController()

# Auth
auth = auth_controller.ensure_authenticated

@router.post("/start_game/{target_player_username}", response_model=Game)
async def start_game(request:Request, target_player_username: str):
    requesting_player = auth_controller.get_user_from_session(request)
    target_player = await user_controller.get_item(target_player_username)

    result = await controller.create(requesting_player, target_player)
    return result

@router.post("/{id}/action", response_model=Game)
async def execute_game_action(request:Request, id: str, action: ChessAction):
    requesting_player = auth_controller.get_user_from_session(request)
    result = await controller.update(id, action, requesting_player)
    return result

@router.get("/{id}", response_model=Game)
async def get_game(id: str):
    result = await controller.get(id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return result

@router.get("", response_model=list[Game])
async def get_games(request: Request, user = Depends(auth)):
    user = auth_controller.ensure_authenticated(request)
    result = await controller.get_all_active_games_by_user(user.username)
    return result