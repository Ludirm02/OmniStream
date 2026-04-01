from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.engine.recommender import RecommenderService
from app.models import Content, Interaction, User
from app.schemas.contracts import (
    ContentCard,
    DailyFeedResponse,
    InteractionRequest,
    RabbitHoleResponse,
    RecommendationRequest,
    RecommendationResponse,
    ResumeResponse,
    UserBootstrapRequest,
    UserResponse,
    VibeOption,
    VibesResponse,
)

router = APIRouter(prefix="/api", tags=["omnistream"])


VIBES = [
    VibeOption(id="focus", label="Deep Focus", objective="Deep work with minimal distraction"),
    VibeOption(id="chill", label="Chill", objective="Low cognitive load and smooth unwind"),
    VibeOption(id="learn", label="Learn", objective="High learning return per minute"),
    VibeOption(id="commute", label="Commute", objective="Mobile-friendly content on the move"),
    VibeOption(id="late_night", label="Late Night", objective="Calm and restorative exploration"),
    VibeOption(id="explore", label="Explore", objective="Balanced cross-domain discovery"),
]



def _service(db: Session, request: Request) -> RecommenderService:
    return RecommenderService(db=db, embedding_service=request.app.state.embedding_service)


@router.get("/vibes", response_model=VibesResponse)
def get_vibes() -> VibesResponse:
    return VibesResponse(vibes=VIBES)


@router.post("/users/bootstrap", response_model=UserResponse)
def bootstrap_user(payload: UserBootstrapRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = User(id=f"user-{uuid4().hex[:10]}", name=payload.name)
    db.add(user)
    db.commit()
    return UserResponse(id=user.id, name=user.name, preferred_vibe=user.preferred_vibe)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user.id, name=user.name, preferred_vibe=user.preferred_vibe)


@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    payload: RecommendationRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="Unknown user. Please bootstrap first.")
    return _service(db, request).recommend(payload)


@router.post("/interactions")
def add_interaction(payload: InteractionRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.get(Content, payload.content_id) is None:
        raise HTTPException(status_code=404, detail="Content not found")

    interaction = Interaction(
        user_id=payload.user_id,
        content_id=payload.content_id,
        action=payload.action,
        time_spent_seconds=payload.time_spent_seconds,
        completion_ratio=payload.completion_ratio,
        vibe=payload.vibe,
        device=payload.device,
        session_minutes=payload.session_minutes,
        occurred_at=datetime.now(UTC),
    )
    db.add(interaction)
    db.commit()

    user = db.get(User, payload.user_id)
    if user and payload.vibe:
        user.preferred_vibe = payload.vibe
        db.commit()

    return {"status": "ok"}


@router.get("/resume/{user_id}", response_model=ResumeResponse)
def get_resume(user_id: str, request: Request, db: Session = Depends(get_db)) -> ResumeResponse:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _service(db, request).resume(user_id)


@router.get("/daily-feed/{user_id}", response_model=DailyFeedResponse)
def get_daily_feed(
    user_id: str,
    request: Request,
    device: str = "mobile",
    db: Session = Depends(get_db),
) -> DailyFeedResponse:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _service(db, request).daily_feed(user_id=user_id, device=device)


@router.get("/rabbit-hole/{content_id}", response_model=RabbitHoleResponse)
def rabbit_hole(
    content_id: str,
    user_id: str,
    request: Request,
    vibe: str = "explore",
    db: Session = Depends(get_db),
) -> RabbitHoleResponse:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return _service(db, request).rabbit_hole(content_id, user_id=user_id, vibe=vibe)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/content", response_model=list[ContentCard])
def list_content(domain: str | None = None, limit: int = 50, db: Session = Depends(get_db)) -> list[ContentCard]:
    stmt = select(Content)
    if domain:
        stmt = stmt.where(Content.domain == domain)

    rows = db.execute(stmt.limit(limit)).scalars().all()

    cards: list[ContentCard] = []
    for row in rows:
        cards.append(
            ContentCard(
                id=row.id,
                title=row.title,
                domain=row.domain,
                description=row.description,
                source=row.source,
                url=row.url,
                duration_minutes=row.duration_minutes,
                tags=json.loads(row.tags_json),
                mood_score=row.mood_score,
                energy_score=row.energy_score,
            )
        )
    return cards
