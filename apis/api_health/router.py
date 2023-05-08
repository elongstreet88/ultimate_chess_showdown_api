from fastapi import APIRouter

# Router
router = APIRouter(
    prefix  = "/health",
    tags    = ["API Health Information"]
)

@router.get("")
def health():
    """
    Return status code 200 OK if healthy.
    """
    return "OK"