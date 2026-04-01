import {
  RabbitHoleResponse,
  RecommendationResponse,
  ResumeResponse,
  VibeOption,
} from "@/types/omnistream";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getVibes() {
  return request<{ vibes: VibeOption[] }>("/api/vibes");
}

export function getRecommendations(payload: {
  user_id: string;
  vibe: string;
  device: string;
  session_minutes: number;
  limit?: number;
}) {
  return request<RecommendationResponse>("/api/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logInteraction(payload: {
  user_id: string;
  content_id: string;
  action: "view" | "click" | "like" | "skip" | "complete";
  time_spent_seconds: number;
  completion_ratio: number;
  vibe: string;
  device: string;
  session_minutes: number;
}) {
  return request<{ status: string }>("/api/interactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getResume(userId: string) {
  return request<ResumeResponse>(`/api/resume/${userId}`);
}

export function getRabbitHole(contentId: string, userId: string, vibe: string) {
  const params = new URLSearchParams({ user_id: userId, vibe });
  return request<RabbitHoleResponse>(`/api/rabbit-hole/${contentId}?${params.toString()}`);
}

export function bootstrapUser(name: string) {
  return request<{ id: string; name: string; preferred_vibe: string | null }>("/api/users/bootstrap", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}
