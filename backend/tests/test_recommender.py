from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.engine.embedding import EmbeddingService
from app.engine.recommender import RecommenderService
from app.engine.seed import seed_database
from app.models import Base, User
from app.schemas.contracts import RecommendationRequest



def _make_db() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = session_local()
    seed_database(db)
    if not db.get(User, "demo-user"):
        db.add(User(id="demo-user", name="Demo User"))
        db.commit()
    return db


def test_recommendation_cross_domain_mix() -> None:
    db = _make_db()
    service = RecommenderService(db, EmbeddingService(dim=96))

    response = service.recommend(
        RecommendationRequest(
            user_id="demo-user",
            vibe="learn",
            device="desktop",
            session_minutes=45,
            local_timestamp=datetime.now(UTC),
            limit=12,
        )
    )

    domains = {item.domain for item in response.recommendations[:8]}
    assert len(domains) >= 3
    assert response.bundles


def test_rabbit_hole_is_cross_domain() -> None:
    db = _make_db()
    service = RecommenderService(db, EmbeddingService(dim=96))

    hole = service.rabbit_hole("vid_ai_teardown", user_id="demo-user", vibe="explore")
    domains = {item.domain for item in hole.journey}

    assert len(hole.journey) >= 3
    assert "video" not in domains
