import asyncio
from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel
from typing import Optional
from enum import Enum
import chess
import uuid
import aioredis
import json

# Router
router = APIRouter(
    prefix="/game",
    tags=["Game"]
)

# Websocket connections
connected_clients = set()

class ActionType(str, Enum):
    MOVE = "MOVE"
    OFFER_DRAW = "OFFER_DRAW"
    ACCEPT_DRAW = "ACCEPT_DRAW"
    RESIGN = "RESIGN"

class ChessAction(BaseModel):
    action_type: ActionType
    move: Optional[str]

class Game:
    def __init__(self):
        self.board = chess.Board()

async def broadcast_message(message: str):
    for client in connected_clients:
        await client.send_text(message)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    redis = await get_redis()
    while True:
        game_id = await websocket.receive_text()
        game = await get_game(redis, game_id)
        if game is not None:
            await websocket.send_text(game.board.fen())
        await asyncio.sleep(0)

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    redis = await get_redis()
    while True:
        game = await get_game(redis, game_id)
        if game is not None:
            await websocket.send_text(game.board.fen())
        #await asyncio.sleep(1)

async def get_redis():
    redis = aioredis.from_url("redis://localhost")
    return redis

async def set_game(redis, game_id, game):
    key = f"game:{game_id}"
    await redis.set(key, json.dumps({"fen": game.board.fen()}))

async def get_game(redis, game_id):
    key = f"game:{game_id}"
    game_data = await redis.get(key)
    if game_data is None:
        return None
    game_data = json.loads(game_data)
    game = Game()
    game.board.set_fen(game_data["fen"])
    return game

async def delete_game(redis, game_id):
    key = f"game:{game_id}"
    await redis.delete(key)

@router.post("/start_game")
async def start_game():
    game_id = str(uuid.uuid4())
    game = Game()
    redis = await get_redis()
    await set_game(redis, game_id, game)
    await redis.close()
    return {"game_id": game_id}

@router.post("/{game_id}/action")
async def game_action(game_id: str, action: ChessAction):
    redis = await get_redis()
    game = await get_game(redis, game_id)

    if game is None:
        await redis.close()
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
        await delete_game(redis, game_id)

    elif action.action_type == ActionType.OFFER_DRAW:
        # Implement draw offer logic here
        pass

    elif action.action_type == ActionType.ACCEPT_DRAW:
        # Implement draw acceptance logic here
        pass

    await set_game(redis, game_id, game)
    await broadcast_message(game.board.fen())

    # Evaluate the position using python-chess
    evaluation = game.board.piece_map()

    # Count the material for each side
    material_white = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.WHITE)
    material_black = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.BLACK)

    # Calculate the evaluation score
    score = material_white - material_black

    await redis.close()

    return {"board": str(game.board), "fen": game.board.fen(), "evaluation": score}

@router.get("/{game_id}")
async def get_game_position(game_id: str):
    redis = await get_redis()
    game = await get_game(redis, game_id)
    if game is None:
        await redis.close()
        raise HTTPException(status_code=404, detail="Game not found")

    await redis.close()

    return {"position": game.board.fen()}

