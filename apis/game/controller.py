import logging
from fastapi import APIRouter, HTTPException, WebSocket
import chess
import uuid
from redis import Redis, asyncio as aioredis
import json
from starlette.responses import StreamingResponse
from apis.game.models import ActionType, ChessAction, Game
from tools.config.app_settings import app_settings

# Redis Connection Pool from url
redis:Redis = aioredis.from_url(app_settings.redis_url)

# Websocket connections
active_websockets:dict[str, list[WebSocket]] = {}

class GameController:
    async def create_game(self) -> Game:
        game = Game(id=str(uuid.uuid4()), fen=chess.STARTING_FEN)
        await self.set_game(game)
        return game

    async def get_game(self, game_id)->Game:
        raw_game = await redis.hget(Game.__name__, game_id)
        if raw_game is None:
            return None
        game = Game.parse_raw(raw_game)
        return game
        
    async def set_game(self, game:Game):
        await redis.hset(Game.__name__, game.id, json.dumps(game.model_dump()))

    async def delete_game(self, game_id):
        key = f"game:{game_id}"
        await redis.delete(key)

    async def execute_action(self, game_id:str, action:ChessAction):
        game = await self.get_game(game_id)

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        if action.action_type == ActionType.MOVE:
            if action.move is None:
                raise HTTPException(status_code=400, detail="Move is required for MOVE action")

            try:
                # Load fen into a game and try the move
                board = chess.Board(game.fen)
                board.push_san(action.move)
                game.fen = board.fen()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid move")

        elif action.action_type == ActionType.RESIGN:
            # Implement resignation logic here
            await self.delete_game(game_id)

        elif action.action_type == ActionType.OFFER_DRAW:
            # Implement draw offer logic here
            pass

        elif action.action_type == ActionType.ACCEPT_DRAW:
            # Implement draw acceptance logic here
            pass

        await self.set_game(game)
        await self.broadcast_message(game.fen, game)

        # Evaluate the position using python-chess
        #evaluation = game.board.piece_map()

        # Count the material for each side
        #material_white = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.WHITE)
        #material_black = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.BLACK)

        # Calculate the evaluation score
        #score = material_white - material_black

        return game

    async def get_live_game_updates(self, game_id:str, websocket:WebSocket):
        # Open connection
        await websocket.accept()

        # Ensure the game exists
        game:Game = await self.get_game(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        # Store the websocket connection
        if game.id not in active_websockets:
            active_websockets[game.id] = []
        active_websockets[game.id].append(websocket)

        # Send the current game state
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

    async def broadcast_message(self, message: str, game:Game):
        for websocket in active_websockets.get(game.id, []):
            logging.info(f"Sending message [{message}] for game id [{game.id}] to websocket [{websocket.client}]")
            await websocket.send_text(message)