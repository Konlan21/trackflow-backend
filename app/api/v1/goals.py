"""
Goals endpoints (Phase 5):
  /user/goals        (list, create)
  /user/goals/{id}   (retrieve, update, patch, delete)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.crud import goal as goal_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalRead, GoalUpdate

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalRead])
async def list_goals(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await goal_crud.list_for_user(db, current_user.id)


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(data: GoalCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await goal_crud.create(db, current_user.id, data)


@router.get("/{goalID}", response_model=GoalRead)
async def retrieve_goal(goalID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = await goal_crud.get_for_user(db, current_user.id, goalID)
    if goal is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return goal


@router.put("/{goalID}", response_model=GoalRead)
@router.patch("/{goalID}", response_model=GoalRead)
async def update_goal(
    goalID: uuid.UUID,
    data: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = await goal_crud.get_for_user(db, current_user.id, goalID)
    if goal is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    return await goal_crud.update(db, goal, data)


@router.delete("/{goalID}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goalID: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    goal = await goal_crud.get_for_user(db, current_user.id, goalID)
    if goal is None:
        raise HTTPException(status_code=404, detail={"detail": "Not found."})
    await goal_crud.delete(db, goal)