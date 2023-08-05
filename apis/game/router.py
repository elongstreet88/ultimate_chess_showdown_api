from fastapi import APIRouter, HTTPException, WebSocket
from apis.game.controller import GameController
from apis.game.models import ChessAction, Game

# Router
router = APIRouter(
    prefix="/game",
    tags=["Game"]
)

# Define Controller
controller = GameController()

@router.websocket("/ws/{game_id}")
async def get_live_game_updates(websocket: WebSocket, game_id: str):
    await controller.get_live_game_updates(game_id, websocket)

@router.post("/start_game", response_model=Game)
async def start_game():
    result = await controller.create_game()
    return result

@router.post("/{game_id}/action", response_model=Game)
async def execute_game_action(game_id: str, action: ChessAction):
    result = await controller.execute_action(game_id, action)
    return result

@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: str):
    result = await controller.get_game(game_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return result