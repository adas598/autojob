from sqlalchemy import Enum, Integer, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Portal, ScrapeRunStatus, UUIDPrimaryKeyMixin


class ScrapeRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scrape_runs"

    portal: Mapped[Portal] = mapped_column(Enum(Portal, name="portal_enum"))
    status: Mapped[ScrapeRunStatus] = mapped_column(
        Enum(ScrapeRunStatus, name="scrape_run_status_enum")
    )
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))
    finished_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
