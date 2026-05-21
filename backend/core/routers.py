from fastapi import FastAPI

from routes.candidates import router as candidates_router
from routes.jobs import router as jobs_router
from routes.interviews import router as interviews_router
from routes.embeddings import router as embeddings_router
from routes.upload import router as upload_router
from routes.match import router as match_router
from routes.analytics import router as analytics_router
from routes.publish import router as publish_router
from routes.intake import router as intake_router
from routes.auth import router as auth_router
from routes.applications import router as applications_router
from routes.chat import router as chat_router
from routes.apply import router as apply_router

_V1 = "/api/v1"

_ROUTERS = [
    (auth_router,         f"{_V1}/auth",          ["Auth"]),
    (candidates_router,   f"{_V1}/candidates",    ["Candidates"]),
    (jobs_router,         f"{_V1}/jobs",          ["Jobs"]),
    (applications_router, f"{_V1}/applications",  ["Applications"]),
    (chat_router,         f"{_V1}/chat",          ["Chat"]),
    (interviews_router,   f"{_V1}/interviews",    ["Interviews"]),
    (embeddings_router,   f"{_V1}/embeddings",    ["Embeddings"]),
    (upload_router,       f"{_V1}/upload",        ["Upload"]),
    (match_router,        f"{_V1}/match",         ["Match"]),
    (analytics_router,    f"{_V1}/analytics",     ["Analytics"]),
    (publish_router,      f"{_V1}/jobs",          ["Publish"]),
    (intake_router,       f"{_V1}/intake",        ["Intake"]),
    (apply_router,        "",                     ["Apply"]),
]


def register_routers(app: FastAPI) -> None:
    for router, prefix, tags in _ROUTERS:
        app.include_router(router, prefix=prefix, tags=tags)
