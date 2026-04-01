# OmniStream AI

OmniStream AI is a **cross-domain recommendation decision assistant** that unifies videos, music, podcasts, movies, and news in one interface.

It goes beyond “watch/listen this” and recommends **what to do right now** based on vibe, context, and behavior.

## Why this stands out

- Context-aware ranking: adjusts by time segment, device, session length, and vibe.
- Cross-domain bundles: generates multi-format packs (for example video + podcast + music).
- Explainable recommendations: every recommendation includes human-readable reasons.
- Rabbit-hole exploration: jump from one item into related items in other domains.
- Resume lane + user memory: interaction history influences future ranking.

## Architecture

- Frontend: Next.js (App Router) + Tailwind CSS
- Backend: FastAPI + SQLAlchemy
- Data: SQLite (seeded catalog)
- Ranking: Hybrid strategy
  - Semantic similarity (local embedding service)
  - Context scoring
  - Diversity balancing across domains
  - Freshness + behavioral weighting

## Core Features Implemented

- Vibe selector: `focus`, `chill`, `learn`, `commute`, `late_night`, `explore`
- Personalized “For You” feed
- Cross-domain bundles section
- Explainability text on every card
- “Dive deeper” rabbit-hole journey
- Continue exploring (resume unfinished content)
- New user profile creation and memory updates through interactions

## How To Run

## Option A: From project root

```bash
make backend-install
make frontend-install
```

Then run in two terminals:

```bash
make backend-dev
```

```bash
make frontend-dev
```

## Option B: Run inside each folder

## 1) Backend (`/backend`)

```bash
cd backend
make backend-install
make backend-dev
```

Backend runs on `http://localhost:8000`.

## 2) Frontend (`/frontend`)

```bash
cd frontend
cp .env.local.example .env.local
make frontend-install
make frontend-dev
```

Frontend runs on `http://localhost:3000`.

## API Highlights

- `GET /health`
- `GET /api/vibes`
- `POST /api/users/bootstrap`
- `POST /api/recommendations`
- `POST /api/interactions`
- `GET /api/resume/{user_id}`
- `GET /api/rabbit-hole/{content_id}?user_id=...&vibe=...`

## Tests and Quality Checks

Backend:

```bash
cd backend
make backend-test
```

Frontend:

```bash
cd frontend
make frontend-build
```

## Demo Pitch 

"OmniStream AI is not just a recommender system. It is a cross-platform content decision assistant that uses context, vibe, and behavioral memory to generate explainable, cross-domain content bundles in real time."
