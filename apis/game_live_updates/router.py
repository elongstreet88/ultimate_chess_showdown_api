from fastapi import APIRouter, WebSocket
from apis.games.controller import GameController

# Router
router = APIRouter(
    prefix="/game_live_updates",
    tags=["Game Live Updates"]
)

# Define Controller
controller = GameController()

@router.websocket("/{id}")
async def get(websocket: WebSocket, id: str):
    await controller.get_live_game_updates(id, websocket)