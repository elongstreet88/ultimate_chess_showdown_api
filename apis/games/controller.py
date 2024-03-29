import logging
import random
from fastapi import HTTPException, WebSocket, status
import chess
import uuid
import json
from apis.games.models import ActionType, ChessAction, Game
from apis.users.controller import UserController
from apis.users.models import User
from tools.config.app_settings import app_settings
from tools.redis.redis import redis_client

# Websocket connections
active_websockets:dict[str, list[WebSocket]] = {}

class GameController:
    def __init__(self):
        self.user_controller = UserController()
        
    async def create(self, player1: User, player2: User) -> Game:
        # randomize who is white and who is black
        if bool(uuid.uuid4().int & 1):
            player1, player2 = player2, player1

        game = Game(
            id=str(uuid.uuid4()),
            fen=chess.STARTING_FEN,
            white_player_id=player1.username,
            black_player_id=player2.username
        )
        await self.__set_game(game)

        # Check if white player is a bot and make a move if it is
        if player1.is_bot:
            bot_move_san = self.bot_make_move(game)
            bot_action = ChessAction(action_type=ActionType.MOVE, move=bot_move_san)
            await self.update(game.id, bot_action, player1)

        return game

    async def get(self, game_id)->Game:
        raw_game = await redis_client.hget(Game.__name__, game_id)
        if raw_game is None:
            return None
        game = Game.parse_raw(raw_game)
        return game
    
    def bot_make_move(self, game: Game) -> str:
        board = chess.Board(game.fen)
        legal_moves = list(board.legal_moves)
        move = random.choice(legal_moves)
        return board.san(move)

    async def update(self, game_id:str, action:ChessAction, user:User):
        game = await self.get(game_id)

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Ensure the user is a player in the game
        if user.username not in [game.white_player_id, game.black_player_id]:
            raise HTTPException(status_code=403, detail="User is not a player in this game")
        
        # Ensure it is the user's turn
        if (user.username == game.white_player_id and not game.is_white_turn) or (user.username == game.black_player_id and game.is_white_turn):
            raise HTTPException(status_code=403, detail="It is not your turn")

        if action.action_type == ActionType.MOVE:
            if action.move is None:
                raise HTTPException(status_code=400, detail="Move is required for MOVE action")

            try:
                # Load fen into a game and try the move
                board = chess.Board(game.fen)
                board.push_san(action.move)
                game.fen = board.fen()
                game.is_white_turn = not game.is_white_turn
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

        await self.__set_game(game)
        await self.broadcast_message(game.fen, game)

        # Evaluate the position using python-chess
        #evaluation = game.board.piece_map()

        # Count the material for each side
        #material_white = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.WHITE)
        #material_black = sum(piece.piece_type for piece in evaluation.values() if piece.color == chess.BLACK)

        # Calculate the evaluation score
        #score = material_white - material_black

        next_player = game.white_player_id if game.is_white_turn else game.black_player_id
        next_user:User = await self.user_controller.get_item(next_player)
        if next_user.is_bot:
            bot_move_san = self.bot_make_move(game)
            bot_action = ChessAction(action_type=ActionType.MOVE, move=bot_move_san)
            await self.update(game_id, bot_action, next_user)
        else:
            await self.broadcast_message(game.fen, game)

        return game

    async def get_live_game_updates(self, game_id:str, websocket:WebSocket):
        # Ensure the game exists
        game:Game = await self.get(game_id)
        if game is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Open connection
        await websocket.accept()

        # Store the websocket connection
        if game.id not in active_websockets:
            active_websockets[game.id] = []
        active_websockets[game.id].append(websocket)

        # Send the current game state
        try:
            while True:
                # Wait for a message from the client
                _ = await websocket.receive_text()
        except:
            # On disconnect, remove the websocket from active_websockets
            if game_id in active_websockets:
                active_websockets[game_id].remove(websocket)

    async def broadcast_message(self, message: str, game:Game):
        for websocket in active_websockets.get(game.id, []):
            logging.info(f"Sending message [{message}] for game id [{game.id}] to websocket [{websocket.client}]")
            await websocket.send_text(message)

    async def get_all_games(self) -> list[Game]:
        raw_games = await redis_client.hgetall(Game.__name__)
        games = [Game.parse_raw(raw_game) for raw_game in raw_games.values()]
        return games
            
    async def get_all_active_games_by_user(self, username:str) -> list[Game]:
        games = await self.get_all_games()
        return [game for game in games if game.white_player_id == username or game.black_player_id == username]

    async def __set_game(self, game:Game):
        await redis_client.hset(Game.__name__, game.id, json.dumps(game.model_dump()))