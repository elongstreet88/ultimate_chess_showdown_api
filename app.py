import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from apis.api_health.router import router as health_router
from apis.auth.controller import AuthController, NotAuthenticatedException
from apis.games.router import router as games_router
from apis.users.router import router as users_router
from apis.user.router import router as user_router
from apis.auth.router import router as router_auth
from apis.app.router import router as router_app
from apis.game_live_updates.router import router as router_game_live_updates
from apis.api_docs.router import APIDocs
from tools.config.app_settings import app_settings

# FastAPI app initialization
app = FastAPI(title="Ultimate Chess Showdown", description="Ultimate Chess Showdown")

# Middleware setup
app.add_middleware(SessionMiddleware, secret_key=app_settings.fastapi_session_secret_key)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Auth setup
controller = AuthController()
auth = controller.ensure_authenticated
auth_ws = controller.ensure_authenticated_ws

# Router setup (none websocket)
routers = [
    APIDocs(app),
    health_router, 
    games_router, 
    users_router,
    user_router
]
for router in routers:
    app.include_router(router, prefix="/api/v1", include_in_schema=True, dependencies=[Depends(auth)])

# Router setup (websocket)
routers_ws = [
    router_game_live_updates
]
for router in routers_ws:
    app.include_router(router, prefix="/api/v1", include_in_schema=False, dependencies=[Depends(auth_ws)])

# Mount auth router
app.include_router(router_auth, prefix="", include_in_schema=True)

# Mount the app router
app.include_router(router_app, prefix="", include_in_schema=False, dependencies=[Depends(auth)])

@app.get("/")
async def root():
    """
    Redirects to /app/
    """
    
    return RedirectResponse(url="/app/")

@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_exception_handler(request: Request, exc: NotAuthenticatedException):
    if request.url.path.startswith("/api"):
        return JSONResponse(content={"detail": "Access Denied"}, status_code=403)
    else:
        # return RedirectResponse(url=exc.headers["Location"])
        return RedirectResponse("/auth", status_code=exc.status_code)

# Main entry point
if __name__ == "__main__":
    try:
        uvicorn.run(app="app:app", host='0.0.0.0', port=8000, reload=True)
    except Exception as e:
        print(f"Failed to start the application: {e}")