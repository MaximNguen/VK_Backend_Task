from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.database import get_db
from app.crud.user import crud_user
from app.models import User
from app.schemas import UserLockResponse

router = APIRouter()

@router.post("/", response_model=schemas.user.UserResponse)
async def create_user(
        user_in: schemas.user.UserCreate,
        db: AsyncSession = Depends(get_db)
):
    existing_user = await crud_user.get_by_login(db, login=user_in.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this login already exists"
        )

    user = await crud_user.create(db, obj_in=user_in)
    return user


@router.get("/", response_model=list[schemas.user.UserResponse])
async def get_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    users = await crud_user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/{user_id}/lock", response_model=UserLockResponse)
async def acquire_lock(
        user_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    user = await crud_user.get(db, user_id=user_id)
    if not user:
        return UserLockResponse(
            success=False,
            message="User not found"
        )

    if user.is_locked():
        return UserLockResponse(
            success=False,
            message="User already locked"
        )

    locktime = int(datetime.now(timezone.utc).timestamp())
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(locktime=locktime)
    )
    await db.commit()

    return UserLockResponse(
        success=True,
        message="User locked successfully",
        locktime=locktime
    )


@router.post("/{user_id}/unlock", response_model=schemas.user.UserLockResponse)
async def release_lock(
        user_id: UUID,
        db: AsyncSession = Depends(get_db)
):
    success = await crud_user.release_lock(db, user_id=user_id)
    if not success:
        return schemas.user.UserLockResponse(
            success=False,
            message="User not found"
        )

    return schemas.user.UserLockResponse(
        success=True,
        message="User unlocked successfully"
    )