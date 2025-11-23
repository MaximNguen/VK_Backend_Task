import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    login = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    env = Column(String(50), nullable=False, index=True)
    domain = Column(String(50), nullable=False, default="regular")
    locktime = Column(BigInteger, nullable=True, index=True)

    def is_locked(self) -> bool:
        if self.locktime is None:
            return False
        lock_time = datetime.fromtimestamp(self.locktime, tz=timezone.utc).replace(tzinfo=None)
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)
        return (current_time - lock_time).total_seconds() < 1800