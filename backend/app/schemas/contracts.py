from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Domain = Literal["video", "music", "podcast", "movie", "news"]
Vibe = Literal["focus", "chill", "learn", "commute", "late_night", "explore"]
Device = Literal["mobile", "desktop", "tablet", "tv"]


class UserBootstrapRequest(BaseModel):
    name: str = Field(default="Demo User", min_length=2, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    preferred_vibe: str | None = None


class ContentCard(BaseModel):
    id: str
    title: str
    domain: Domain
    description: str
    source: str
    url: str
    duration_minutes: float
    tags: list[str]
    mood_score: float
    energy_score: float


class RecommendationCard(ContentCard):
    score: float
    explanation: str
    rank_reasons: list[str]


class BundleCard(BaseModel):
    name: str
    vibe: str
    expected_minutes: int
    explanation: str
    items: list[RecommendationCard]


class ContextSummary(BaseModel):
    vibe: str
    time_segment: str
    device: str
    session_minutes: int
    objective: str


class UserInsights(BaseModel):
    top_tags: list[str]
    dominant_domains: list[str]
    curiosity_score: float
    momentum_label: str


class RecommendationRequest(BaseModel):
    user_id: str
    vibe: Vibe = "explore"
    device: Device = "desktop"
    session_minutes: int = Field(default=30, ge=5, le=240)
    local_timestamp: datetime | None = None
    limit: int = Field(default=16, ge=4, le=30)


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationCard]
    bundles: list[BundleCard]
    context: ContextSummary
    insights: UserInsights
    generated_at: datetime


class InteractionRequest(BaseModel):
    user_id: str
    content_id: str
    action: Literal["view", "click", "like", "skip", "complete"] = "view"
    time_spent_seconds: int = Field(default=0, ge=0)
    completion_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    vibe: str | None = None
    device: str | None = None
    session_minutes: int | None = Field(default=None, ge=1, le=240)


class ResumeItem(BaseModel):
    content: ContentCard
    completion_ratio: float
    time_spent_seconds: int
    last_seen_at: datetime


class ResumeResponse(BaseModel):
    user_id: str
    items: list[ResumeItem]


class RabbitHoleResponse(BaseModel):
    seed: RecommendationCard
    journey: list[RecommendationCard]


class VibeOption(BaseModel):
    id: str
    label: str
    objective: str


class VibesResponse(BaseModel):
    vibes: list[VibeOption]
