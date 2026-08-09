from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.tracker import router as tracker_router
from app.api.v1.budgets import router as budgets_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.goals import router as goals_router
from app.api.v1.ai import router as ai_router
from app.api.v1.exports import router as exports_router

api_router = APIRouter()
api_router.include_router(accounts_router, prefix="/auth")
api_router.include_router(tracker_router, prefix="/user")
api_router.include_router(budgets_router, prefix="/user")
api_router.include_router(analytics_router, prefix="/user")
api_router.include_router(goals_router, prefix="/user")
api_router.include_router(ai_router, prefix="/user")
api_router.include_router(exports_router, prefix="/user")