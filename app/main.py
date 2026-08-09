"""
Mirrors expense_tracker/urls.py + expense_tracker/settings.py entrypoint.
- /auth/*   -> accounts endpoints
- /user/*   -> tracker (income/expenditure/ai-query/dashboard) endpoints
- /docs, /redoc, /openapi.json -> built-in, replaces drf-spectacular
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_logging
# from app.db.base import Base, engine

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
)

if settings.CORS_ALLOW_ALL_ORIGINS:
    cors_origins = ["*"]
else:
    cors_origins = settings.CORS_ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not settings.CORS_ALLOW_ALL_ORIGINS,  # can't combine "*" with credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router)
