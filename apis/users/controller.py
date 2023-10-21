from datetime import datetime
from apis.users.models import User
from tools.redis.redis import redis_client

class UserController:
    USERS_KEY = "Users"

    async def create(self, user: User) -> User:
        serialized_user = user.json()
        await redis_client.hset(self.USERS_KEY, user.username, serialized_user)
        return user

    async def get_item(self, username: str) -> User:
        user_str = await redis_client.hget(self.USERS_KEY, username)
        if not user_str:
            return None
        user_data = User.parse_raw(user_str.decode())
        return user_data
    
    async def get_users(self, exclude_user:User) -> list[User]:
        raw_users = await redis_client.hgetall(self.USERS_KEY)
        users = [User.parse_raw(user.decode()) for user in raw_users.values()]
        if exclude_user:
            users = [user for user in users if user.username != exclude_user.username]
        return users

    async def update_last_login(self, username: str) -> None:
        user = await self.get_item(username)
        if user:
            user.last_login = datetime.utcnow()
            await self.create(user)

    async def seed(self) -> None:
        bots = [
            User(username="bot1", email="bot1@ultimatecs.onrender.com", full_name="Bot 1", last_login=datetime.utcnow(), is_bot=True),
            User(username="bot2", email="bot2@ultimatecs.onrender.com", full_name="Bot 2", last_login=datetime.utcnow(), is_bot=True),
        ]

        for bot in bots:
            if not await self.get_item(bot.username):
                await self.create(bot)
