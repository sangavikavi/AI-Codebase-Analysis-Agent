import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "zip" or "github"
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repo_path: Mapped[str] = mapped_column(String(500), nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="created", index=True)  # created, preprocessing, analyzing, paused, completed, failed
    personas: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["sde", "pm"]
    config: Mapped[dict] = mapped_column(JSON, default=dict)    # depth, verbosity, toggles, diagrams

    detected_stack: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entry_points: Mapped[list] = mapped_column(JSON, default=list)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    endpoint_count: Mapped[int] = mapped_column(Integer, default=0)

    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    current_stage: Mapped[str] = mapped_column(String(100), default="Initialized")
    current_file: Mapped[str] = mapped_column(String(255), default="")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="projects")
    events = relationship("ActivityEvent", back_populates="project", cascade="all, delete-orphan", order_by="ActivityEvent.timestamp")
    reports = relationship("ProjectReport", back_populates="project", cascade="all, delete-orphan")
    chat_logs = relationship("AnalysisChat", back_populates="project", cascade="all, delete-orphan", order_by="AnalysisChat.timestamp")
