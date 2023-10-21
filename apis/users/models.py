from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    username: str
    email: str
    full_name: str = None
    last_login: datetime = None
    is_bot: bool = False