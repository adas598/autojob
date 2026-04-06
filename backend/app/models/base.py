from datetime import datetime, timezone

from sqlalchemy import DateTime, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


@event.listens_for(Base, "before_update", propagate=True)
def _set_updated_at(mapper, connection, target):  # noqa: ARG001
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(timezone.utc)
