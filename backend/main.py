from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.app_factory import create_app

app = create_app()

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
_health_router = APIRouter(tags=["Health"])


@_health_router.get(
    "/health",
    summary="Health check",
    response_description="Service liveness status",
    responses={200: {"content": {"application/json": {"example": {"status": "ok", "version": "1.0.0"}}}}},
)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "version": "1.0.0"})


app.include_router(_health_router)
