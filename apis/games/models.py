from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ActionType(str, Enum):
    MOVE = "MOVE"
    OFFER_DRAW = "OFFER_DRAW"
    ACCEPT_DRAW = "ACCEPT_DRAW"
    RESIGN = "RESIGN"

class ChessAction(BaseModel):
    action_type: ActionType
    move: Optional[str]

class Game(BaseModel):
    id              : str
    fen             : str
    white_player_id : str
    black_player_id : str