from sqlalchemy import Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UsageOperation


class UsageLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usage_logs"

    operation: Mapped[UsageOperation] = mapped_column(
        Enum(UsageOperation, name="usage_operation_enum")
    )
    model: Mapped[str] = mapped_column(String(100))
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
