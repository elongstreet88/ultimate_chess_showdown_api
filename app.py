import logging
import uvicorn
from fastapi import FastAPI
from apis.api_docs.router import APIDocs
from apis.api_health.router import router as router_health
from apis.game.router import router as router_game
from fastapi.middleware.gzip import GZipMiddleware
from tools.logs.logs import LOGGING_CONFIG
from tools.logs.logs import get_logger
from fastapi.middleware.cors import CORSMiddleware

# Create logger
#logging.config.dictConfig(LOGGING_CONFIG)
#logger = get_logger(__name__)

# Fast API
app = FastAPI(
    title        = "Ultimate Chess Showdown",
    description  = "Ultimate Chess Showdown",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware, 
    allow_credentials=True,
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Add GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# routers
routers = [
    APIDocs(app),
    router_health,
    router_game
]

# Add routers
for router in routers:
    app.include_router(
        prefix="/api/v1", 
        include_in_schema=True,
        router=router
    )

@app.on_event("startup")
async def startup():
    ...

# Start the application if called directly
if __name__ == "__main__":
    try:
        uvicorn.run(
            app         = app if not app.debug else "app:app", # Required to allow reload to work in debug mode
            host        = '0.0.0.0', 
            port        = 8000, 
            reload      = app.debug
        )
        
    except Exception as e:
        logger.error(f"Failed to start the application: {e}")