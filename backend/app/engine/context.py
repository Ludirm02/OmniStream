from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


VIBE_CONFIG = {
    "focus": {
        "objective": "Deep work with minimal distraction",
        "energy_target": 0.45,
        "domain_boost": {"music": 1.15, "podcast": 1.12, "video": 1.05, "news": 0.92, "movie": 0.85},
    },
    "chill": {
        "objective": "Low cognitive load and smooth unwind",
        "energy_target": 0.24,
        "domain_boost": {"music": 1.18, "movie": 1.08, "podcast": 1.05, "video": 0.94, "news": 0.85},
    },
    "learn": {
        "objective": "High learning return per minute",
        "energy_target": 0.62,
        "domain_boost": {"video": 1.15, "podcast": 1.12, "news": 1.08, "movie": 0.88, "music": 0.9},
    },
    "commute": {
        "objective": "Mobile-friendly content during movement",
        "energy_target": 0.58,
        "domain_boost": {"podcast": 1.16, "music": 1.13, "news": 1.06, "video": 0.9, "movie": 0.76},
    },
    "late_night": {
        "objective": "Calm and restorative exploration",
        "energy_target": 0.2,
        "domain_boost": {"music": 1.2, "podcast": 1.08, "movie": 1.04, "video": 0.94, "news": 0.82},
    },
    "explore": {
        "objective": "Balanced cross-domain discovery",
        "energy_target": 0.5,
        "domain_boost": {"music": 1.0, "podcast": 1.0, "video": 1.0, "news": 1.0, "movie": 1.0},
    },
}


@dataclass(slots=True)
class RuntimeContext:
    vibe: str
    objective: str
    time_segment: str
    device: str
    session_minutes: int
    energy_target: float
    domain_boost: dict[str, float]
    duration_target: int



def infer_time_segment(ts: datetime) -> str:
    hour = ts.hour
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 16:
        return "midday"
    if 16 <= hour < 21:
        return "evening"
    return "night"



def build_context(vibe: str, device: str, session_minutes: int, ts: datetime) -> RuntimeContext:
    cfg = VIBE_CONFIG.get(vibe, VIBE_CONFIG["explore"])
    time_segment = infer_time_segment(ts)
    domain_boost = dict(cfg["domain_boost"])
    energy_target = float(cfg["energy_target"])

    if time_segment == "morning":
        domain_boost["news"] *= 1.08
        domain_boost["podcast"] *= 1.05
        energy_target += 0.08
    elif time_segment == "night":
        domain_boost["music"] *= 1.08
        domain_boost["movie"] *= 1.06
        domain_boost["news"] *= 0.85
        energy_target -= 0.1

    if device == "mobile":
        domain_boost["podcast"] *= 1.06
        domain_boost["news"] *= 1.05
        domain_boost["movie"] *= 0.84
    elif device == "tv":
        domain_boost["movie"] *= 1.12
        domain_boost["video"] *= 1.08

    duration_target = max(5, min(55, int(session_minutes / 2.6)))

    return RuntimeContext(
        vibe=vibe,
        objective=cfg["objective"],
        time_segment=time_segment,
        device=device,
        session_minutes=session_minutes,
        energy_target=max(0.05, min(0.95, energy_target)),
        domain_boost=domain_boost,
        duration_target=duration_target,
    )


def duration_alignment(duration_minutes: float, target: int) -> float:
    max_gap = max(12, target)
    gap = abs(duration_minutes - target)
    score = 1.0 - min(1.0, gap / max_gap)
    return max(0.0, score)
