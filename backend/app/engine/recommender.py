from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.engine.context import RuntimeContext, build_context, duration_alignment
from app.engine.embedding import EmbeddingService, cosine_similarity, recency_decay
from app.models import Content, Interaction
from app.schemas.contracts import (
    BundleCard,
    ContentCard,
    ContextSummary,
    RabbitHoleResponse,
    RecommendationCard,
    RecommendationRequest,
    RecommendationResponse,
    ResumeItem,
    ResumeResponse,
    UserInsights,
)


@dataclass(slots=True)
class IndexedContent:
    row: Content
    tags: list[str]
    embedding: np.ndarray


class RecommenderService:
    def __init__(self, db: Session, embedding_service: EmbeddingService) -> None:
        self.db = db
        self.embedding_service = embedding_service
        self.index = self._load_index()
        self.content_by_id = {item.row.id: item for item in self.index}
        self.global_vector = self._global_vector()

    def recommend(self, payload: RecommendationRequest) -> RecommendationResponse:
        now = payload.local_timestamp or datetime.now(UTC)
        ctx = build_context(payload.vibe, payload.device, payload.session_minutes, now)
        user_vector, tag_counter, domain_counter, momentum = self._user_profile(payload.user_id)
        seen_recent = self._recent_content_ids(payload.user_id)

        scored: list[RecommendationCard] = []
        total_interactions = max(1, sum(domain_counter.values()))

        for item in self.index:
            base_sim = cosine_similarity(user_vector, item.embedding)
            context_score = self._context_score(item, ctx, tag_counter)
            diversity_score = 1.0 - min(0.75, domain_counter.get(item.row.domain, 0) / total_interactions)
            published_at = item.row.published_at
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)
            days_old = max(0, (now - published_at).days)
            freshness = recency_decay(days_old)

            score = (
                0.52 * base_sim
                + 0.3 * context_score
                + 0.1 * diversity_score
                + 0.08 * freshness
            )

            if item.row.id in seen_recent:
                score -= 0.12

            reasons = self._reasons(item, ctx, tag_counter, base_sim)
            scored.append(
                RecommendationCard(
                    **self._content_card(item).model_dump(),
                    score=round(score, 4),
                    explanation=self._explanation(item, ctx, reasons),
                    rank_reasons=reasons,
                )
            )

        ranked = sorted(scored, key=lambda x: x.score, reverse=True)[: payload.limit]
        bundles = self._build_bundles(ranked, payload.vibe)

        return RecommendationResponse(
            recommendations=ranked,
            bundles=bundles,
            context=ContextSummary(
                vibe=payload.vibe,
                time_segment=ctx.time_segment,
                device=payload.device,
                session_minutes=payload.session_minutes,
                objective=ctx.objective,
            ),
            insights=self._insights(tag_counter, domain_counter, momentum),
            generated_at=datetime.now(UTC),
        )

    def rabbit_hole(self, seed_id: str, user_id: str, vibe: str = "explore") -> RabbitHoleResponse:
        seed = self.content_by_id.get(seed_id)
        if not seed:
            raise ValueError(f"Unknown content id: {seed_id}")

        user_vector, tag_counter, _, _ = self._user_profile(user_id)
        ctx = build_context(vibe, "desktop", 30, datetime.now(UTC))

        journey: list[RecommendationCard] = []
        used_domains = {seed.row.domain}
        for item in sorted(
            self.index,
            key=lambda node: cosine_similarity(seed.embedding, node.embedding)
            + 0.35 * cosine_similarity(user_vector, node.embedding)
            + 0.2 * self._context_score(node, ctx, tag_counter),
            reverse=True,
        ):
            if item.row.id == seed.row.id:
                continue
            if item.row.domain in used_domains:
                continue
            used_domains.add(item.row.domain)
            reasons = self._reasons(item, ctx, tag_counter, cosine_similarity(seed.embedding, item.embedding))
            journey.append(
                RecommendationCard(
                    **self._content_card(item).model_dump(),
                    score=round(cosine_similarity(seed.embedding, item.embedding), 4),
                    explanation=self._explanation(item, ctx, reasons),
                    rank_reasons=reasons,
                )
            )
            if len(journey) >= 4:
                break

        seed_card = RecommendationCard(
            **self._content_card(seed).model_dump(),
            score=1.0,
            explanation="This is your selected seed. The journey spans other domains with similar intent.",
            rank_reasons=["seed item"],
        )

        return RabbitHoleResponse(seed=seed_card, journey=journey)

    def resume(self, user_id: str) -> ResumeResponse:
        rows = self.db.execute(
            select(Interaction)
            .where(Interaction.user_id == user_id)
            .order_by(desc(Interaction.occurred_at))
            .limit(40)
        ).scalars()

        seen: set[str] = set()
        items: list[ResumeItem] = []
        for interaction in rows:
            if interaction.content_id in seen:
                continue
            if interaction.completion_ratio >= 0.96:
                continue

            content = self.content_by_id.get(interaction.content_id)
            if not content:
                continue

            seen.add(interaction.content_id)
            items.append(
                ResumeItem(
                    content=self._content_card(content),
                    completion_ratio=interaction.completion_ratio,
                    time_spent_seconds=interaction.time_spent_seconds,
                    last_seen_at=interaction.occurred_at,
                )
            )
            if len(items) >= 8:
                break

        return ResumeResponse(user_id=user_id, items=items)

    def _load_index(self) -> list[IndexedContent]:
        rows = self.db.execute(select(Content)).scalars().all()
        indexed: list[IndexedContent] = []
        for row in rows:
            tags = json.loads(row.tags_json)
            text = f"{row.title}. {row.description}. {' '.join(tags)}"
            indexed.append(IndexedContent(row=row, tags=tags, embedding=self.embedding_service.embed(text)))
        return indexed

    def _global_vector(self) -> np.ndarray:
        if not self.index:
            return np.zeros(self.embedding_service.dim, dtype=np.float32)
        stacked = np.stack([item.embedding for item in self.index])
        mean = np.mean(stacked, axis=0)
        norm = np.linalg.norm(mean)
        if norm <= 1e-12:
            return mean
        return mean / norm

    def _user_profile(self, user_id: str) -> tuple[np.ndarray, Counter[str], Counter[str], float]:
        rows = self.db.execute(
            select(Interaction)
            .where(Interaction.user_id == user_id)
            .order_by(desc(Interaction.occurred_at))
            .limit(80)
        ).scalars().all()

        if not rows:
            return self.global_vector, Counter(), Counter(), 0.5

        vectors: list[np.ndarray] = []
        weights: list[float] = []
        tag_counter: Counter[str] = Counter()
        domain_counter: Counter[str] = Counter()
        completion_values: list[float] = []

        for idx, interaction in enumerate(rows):
            item = self.content_by_id.get(interaction.content_id)
            if not item:
                continue
            recency_weight = 1.0 / (1 + idx * 0.08)
            engagement = 0.4 + interaction.completion_ratio + min(0.5, interaction.time_spent_seconds / 2400)
            weight = recency_weight * engagement
            vectors.append(item.embedding)
            weights.append(weight)
            tag_counter.update(item.tags)
            domain_counter.update([item.row.domain])
            completion_values.append(interaction.completion_ratio)

        if not vectors:
            return self.global_vector, Counter(), Counter(), 0.5

        matrix = np.stack(vectors)
        w = np.array(weights, dtype=np.float32)
        blended = np.average(matrix, axis=0, weights=w)
        norm = np.linalg.norm(blended)
        if norm > 1e-12:
            blended = blended / norm

        momentum = float(sum(completion_values) / max(1, len(completion_values)))
        return blended, tag_counter, domain_counter, momentum

    def _recent_content_ids(self, user_id: str) -> set[str]:
        rows = self.db.execute(
            select(Interaction.content_id)
            .where(Interaction.user_id == user_id)
            .order_by(desc(Interaction.occurred_at))
            .limit(12)
        ).all()
        return {row[0] for row in rows}

    def _context_score(self, item: IndexedContent, ctx: RuntimeContext, tag_counter: Counter[str]) -> float:
        domain_weight = ctx.domain_boost.get(item.row.domain, 1.0)
        energy_alignment = 1.0 - min(1.0, abs(item.row.energy_score - ctx.energy_target))
        duration_fit = duration_alignment(item.row.duration_minutes, ctx.duration_target)
        tag_bonus = sum(tag_counter.get(tag, 0) for tag in item.tags)
        normalized_tag_bonus = min(1.0, tag_bonus / 10)

        raw = 0.45 * energy_alignment + 0.3 * duration_fit + 0.25 * normalized_tag_bonus
        return max(0.0, min(1.0, raw * domain_weight))

    def _reasons(
        self,
        item: IndexedContent,
        ctx: RuntimeContext,
        tag_counter: Counter[str],
        base_sim: float,
    ) -> list[str]:
        reasons: list[str] = []
        overlap = [tag for tag in item.tags if tag_counter.get(tag, 0) > 0]
        if overlap:
            reasons.append(f"Matches your recurring interests: {', '.join(overlap[:2])}")
        reasons.append(f"Fits your {ctx.vibe.replace('_', ' ')} objective")
        reasons.append(f"Optimized for {ctx.time_segment} sessions on {ctx.device}")
        if base_sim > 0.2:
            reasons.append("Strong semantic similarity with your recent activity")
        return reasons[:3]

    def _explanation(self, item: IndexedContent, ctx: RuntimeContext, reasons: list[str]) -> str:
        if reasons:
            return f"Recommended for {ctx.vibe.replace('_', ' ')} because {reasons[0].lower()}."
        return f"Recommended to balance your {ctx.time_segment} content mix across domains."

    def _content_card(self, item: IndexedContent) -> ContentCard:
        return ContentCard(
            id=item.row.id,
            title=item.row.title,
            domain=item.row.domain,
            description=item.row.description,
            source=item.row.source,
            url=item.row.url,
            duration_minutes=item.row.duration_minutes,
            tags=item.tags,
            mood_score=item.row.mood_score,
            energy_score=item.row.energy_score,
        )

    def _build_bundles(self, ranked: list[RecommendationCard], vibe: str) -> list[BundleCard]:
        if not ranked:
            return []

        bundle_names = {
            "focus": ["Deep Work Pack", "Signal Stack", "Flow Sprint"],
            "chill": ["Soft Landing Pack", "Calm Drift", "Unwind Mix"],
            "learn": ["Learning Arc", "Insight Stack", "Builder Mode"],
            "commute": ["Transit Pack", "City Momentum", "On-the-Go Mix"],
            "late_night": ["Night Reset", "Moonlight Pack", "Quiet Loop"],
            "explore": ["Discovery Pack", "Cross-Stream Mix", "Curiosity Bundle"],
        }

        bundles: list[BundleCard] = []
        used_ids: set[str] = set()

        for bundle_name in bundle_names.get(vibe, bundle_names["explore"]):
            selected: list[RecommendationCard] = []
            used_domains: set[str] = set()
            for card in ranked:
                if card.id in used_ids:
                    continue
                if card.domain in used_domains:
                    continue
                selected.append(card)
                used_domains.add(card.domain)
                used_ids.add(card.id)
                if len(selected) >= 3:
                    break

            if len(selected) < 2:
                break

            expected = int(sum(item.duration_minutes for item in selected))
            bundles.append(
                BundleCard(
                    name=bundle_name,
                    vibe=vibe,
                    expected_minutes=expected,
                    explanation=(
                        f"A cross-domain sequence designed for {vibe.replace('_', ' ')} "
                        f"with {len(selected)} complementary formats."
                    ),
                    items=selected,
                )
            )

        return bundles

    def _insights(self, tag_counter: Counter[str], domain_counter: Counter[str], momentum: float) -> UserInsights:
        top_tags = [tag for tag, _ in tag_counter.most_common(4)] or ["discovering"]
        dominant_domains = [domain for domain, _ in domain_counter.most_common(3)] or ["video", "podcast"]

        unique_domains = len(domain_counter)
        total = max(1, sum(domain_counter.values()))
        curiosity = min(1.0, (unique_domains / 5) * 0.7 + (1 - max(domain_counter.values(), default=0) / total) * 0.3)

        if momentum >= 0.78:
            momentum_label = "Locked In"
        elif momentum >= 0.58:
            momentum_label = "Steady"
        else:
            momentum_label = "Exploring"

        return UserInsights(
            top_tags=top_tags,
            dominant_domains=dominant_domains,
            curiosity_score=round(curiosity, 3),
            momentum_label=momentum_label,
        )
