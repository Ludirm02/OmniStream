from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    preferred_vibe: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    interactions: Mapped[list[Interaction]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Content(Base):
    __tablename__ = "content"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    domain: Mapped[str] = mapped_column(String(24), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False)
    mood_score: Mapped[float] = mapped_column(Float, default=0.5)
    energy_score: Mapped[float] = mapped_column(Float, default=0.5)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    extra_json: Mapped[str] = mapped_column(Text, default="{}")

    interactions: Mapped[list[Interaction]] = relationship(back_populates="content", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    content_id: Mapped[str] = mapped_column(String(64), ForeignKey("content.id"), index=True)
    action: Mapped[str] = mapped_column(String(32), default="view")
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completion_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    vibe: Mapped[str | None] = mapped_column(String(32), nullable=True)
    device: Mapped[str | None] = mapped_column(String(16), nullable=True)
    session_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[User] = relationship(back_populates="interactions")
    content: Mapped[Content] = relationship(back_populates="interactions")
