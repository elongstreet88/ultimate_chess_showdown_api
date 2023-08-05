import asyncio
import logging
from fastapi import APIRouter, HTTPException, WebSocket
import chess
import uuid
from redis import Redis, asyncio as aioredis
import json
from starlette.responses import StreamingResponse
from apis.game.models import ActionType, ChessAction, Game
from tools.config.app_settings import app_settings

# Router
router = APIRouter(
    prefix="/game",
    tags=["Game"]
)

# Redis Connection Pool from url
redis:Redis = aioredis.from_url(app_settings.redis_url)

# Websocket connections
active_websockets:dict[str, list[WebSocket]] = {}

async def broadcast_message(message: str, game_id:str):
    for websocket in active_websockets.get(game_id, []):
        logging.info(f"Sending message [{message}] for game id [{game_id}] to websocket [{websocket.client}]")
        await websocket.send_text(message)

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()

    # Store the websocket connection
    if game_id not in active_websockets:
        active_websockets[game_id] = []
    active_websockets[game_id].append(websocket)

    try:
        while True:
            # Instead of polling the database, just wait for messages or a disconnect from the client.
            data = await websocket.receive_text()
            # Handle this data if needed (like if the client sends any message)
            # For instance, if the client sends a "ping", you can reply with a "pong".
            if data == "ping":
                await websocket.send_text("pong")
    except:
        # On disconnect, remove the websocket from active_websockets
        if game_id in active_websockets:
            active_websockets[game_id].remove(websocket)

async def set_game(game_id, game):
    key = f"game:{game_id}"
    await redis.set(key, json.dumps({"fen": game.board.fen()}))

async def get_game(game_id):
    key = f"game:{game_id}"
    game_data = await redis.get(key)
    if game_data is None:
        return None
    game_data = json.loads(game_data)
    game = Game()
    game.board.set_fen(game_data["fen"])
    return game

async def delete_game(game_id):
    key = f"game:{game_id}"
    await redis.delete(key)

@router.post("/start_game")
async def start_game():
    game_id = str(uuid.uuid4())
    game = Game()
    await set_game(game_id, game)
    return {"game_id": game_id}

@router.post("/{game_id}/action")
async def game_action(game_id: str, action: ChessAction):
    game = await get_game(game_id)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    if action.action_type == ActionType.MOVE:
        if action.move is None:
            raise HTTPException(status_code=400, detail="Move is required for MOVE action")

        try:
            game.board.push_san(action.move)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid move")

    elif action.action_type == ActionType.RESIGN:
        # Implement resignation logic here
        await delete_game(game_id)

    elif action.action_type == ActionType.OFFER_DRAW:
        # Implement draw offer logic here
        pass

    elif action.action_type == ActionType.ACCEPT_DRAW:
        # Implement draw acceptance logic here
        pass

    await set_game(game_id, game)
    await broadcast_message(game.board.fen(), game_id)

    # Evaluate the position using python-chess
    evaluation = game.board.piece_map()

    # Count the material for each side
    material_white = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.WHITE)
    material_black = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.BLACK)

    # Calculate the evaluation score
    score = material_white - material_black

    return {
        "board": str(game.board), 
        "fen": game.board.fen(), 
        "evaluation": score
    }

@router.get("/{game_id}")
async def get_game_position(game_id: str):
    game = await get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {"position": game.board.fen()}

