from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class AnalysisChat(Base):
    __tablename__ = "analysis_chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "agent"
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "question", "context", "refusal", "answer"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="chat_logs")


class AnalysisCheckpoint(Base):
    __tablename__ = "analysis_checkpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # project_id or custom checkpoint ID
    project_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    node_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
