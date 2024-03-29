from datetime import datetime
import os
from fastapi import Depends, HTTPException, Request, WebSocket, status
from fastapi.responses import RedirectResponse
from apis.users.controller import UserController
from apis.users.models import User
from tools.config.app_settings import app_settings
from google_auth_oauthlib.flow import Flow
from tools.redis.redis import redis_client

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from fastapi import HTTPException

class NotAuthenticatedException(HTTPException):
    def __init__(self, detail: str, redirect_url: str):
        super().__init__(status_code=307, detail=detail)
        self.headers = {"Location": redirect_url}



class AuthController:
    def __init__(self):
        self.users_controller = UserController()

    def get_user_from_session(self, request: Request) -> User:
        user = request.session.get("user")
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return User(**user)

    def ensure_authenticated(self, request:Request) -> User|RedirectResponse:
        try:
            return self.get_user_from_session(request)
        except HTTPException:
            raise NotAuthenticatedException(detail="Not authenticated", redirect_url=f"/auth?next={request.url.path}")
        
    def ensure_authenticated_ws(self, websocket: WebSocket) -> User:
        user = websocket.session.get("user")
        if not user:
            websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        return User(**user)
    
    async def login(self, request: Request, next: str = "/"):
        flow = self._create_flow(request, state=next)
        authorization_url, _ = flow.authorization_url(prompt="consent")
        return RedirectResponse(authorization_url)
    
    async def auth_callback(self, request: Request, original_url: str = "/"):
        request_url = str(request.url)
        flow = self._create_flow(request)
        flow.fetch_token(authorization_response=request_url)
        
        session = flow.authorized_session()
        user_info = session.get("https://www.googleapis.com/oauth2/v3/userinfo").json()

        user = User(
            username=user_info["email"],
            email=user_info["email"],
            full_name=user_info["name"],
            last_login=datetime.utcnow()
        )

        request.session["user"] = user.model_dump(mode="json")
        
        # Check if user already exists in Redis
        exists = await self.users_controller.get_item(user.username)
        if exists:
            await self.users_controller.update_last_login(user.username)
        else:
            await self.users_controller.create(user)

        # Redirect to original URL
        return RedirectResponse(url=original_url)
    
    def _create_flow(self, request: Request, state=None) -> Flow:
        base_url = str(request.base_url)
        redirect_uri = f"{base_url.rstrip('/')}/auth/callback"
        
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": app_settings.google_client_id,
                    "client_secret": app_settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            },
            scopes=[
                "openid", 
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile"
            ],
            redirect_uri=redirect_uri,
            state=state
        )
        return flow
    
    async def logout(self, request: Request):
        request.session.clear()
        return RedirectResponse(url="/")
