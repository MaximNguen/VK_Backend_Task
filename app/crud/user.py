from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User
from app.schemas.user import UserCreate, UserLockResponse
from app.services.auth import get_password_hash


class CRUDUser:
    async def get(self, db: AsyncSession, user_id: UUID) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_login(self, db: AsyncSession, login: str) -> User | None:
        result = await db.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def get_multi(
            self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(
            login=obj_in.login,
            password=hashed_password,
            project_id=obj_in.project_id,
            env=obj_in.env,
            domain=obj_in.domain,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def acquire_lock(self, db: AsyncSession, user_id: UUID) -> bool:
        user = await self.get(db, user_id)  # Используй self.get, а не crud_user.get
        if not user:
            return False

        if user.is_locked():
            return False

        locktime = int(datetime.now(timezone.utc).timestamp())
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(locktime=locktime)
        )
        await db.commit()
        return True

    async def release_lock(self, db: AsyncSession, user_id: UUID) -> bool:
        user = await self.get(db, user_id)
        if not user:
            return False

        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(locktime=None)
        )
        await db.commit()
        return True

crud_user = CRUDUser()