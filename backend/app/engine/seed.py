from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.catalog import CONTENT_CATALOG, DEMO_INTERACTIONS
from app.models import Content, Interaction, User


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed_database(db: Session) -> None:
    existing_content = db.scalar(select(Content.id).limit(1))
    if not existing_content:
        for row in CONTENT_CATALOG:
            db.add(
                Content(
                    id=row["id"],
                    title=row["title"],
                    domain=row["domain"],
                    description=row["description"],
                    source=row["source"],
                    url=row["url"],
                    duration_minutes=row["duration_minutes"],
                    language=row.get("language", "en"),
                    tags_json=json.dumps(row["tags"]),
                    mood_score=row["mood_score"],
                    energy_score=row["energy_score"],
                    published_at=_parse_dt(row["published_at"]),
                    extra_json=json.dumps({}),
                )
            )

    demo_user = db.get(User, "demo-user")
    if demo_user is None:
        demo_user = User(id="demo-user", name="Demo User", preferred_vibe="learn")
        db.add(demo_user)

    has_interactions = db.scalar(select(Interaction.id).where(Interaction.user_id == "demo-user").limit(1))
    if not has_interactions:
        now = datetime.now(UTC)
        for idx, row in enumerate(DEMO_INTERACTIONS):
            content_id, action, spent, ratio, vibe, device, session = row
            db.add(
                Interaction(
                    user_id="demo-user",
                    content_id=content_id,
                    action=action,
                    time_spent_seconds=spent,
                    completion_ratio=ratio,
                    vibe=vibe,
                    device=device,
                    session_minutes=session,
                    occurred_at=now - timedelta(hours=idx * 6),
                )
            )

    db.commit()
