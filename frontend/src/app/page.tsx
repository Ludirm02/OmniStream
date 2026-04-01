"use client";

import { useEffect, useMemo, useState } from "react";

import {
  bootstrapUser,
  getRabbitHole,
  getRecommendations,
  getResume,
  getVibes,
  logInteraction,
} from "@/lib/api";
import {
  RabbitHoleResponse,
  RecommendationCard,
  RecommendationResponse,
  ResumeResponse,
  VibeOption,
} from "@/types/omnistream";

const DEVICES = ["desktop", "mobile", "tablet", "tv"];
const DOMAIN_STYLES: Record<string, string> = {
  video: "bg-red-50 text-red-700 border-red-200",
  music: "bg-emerald-50 text-emerald-700 border-emerald-200",
  podcast: "bg-sky-50 text-sky-700 border-sky-200",
  movie: "bg-amber-50 text-amber-700 border-amber-200",
  news: "bg-indigo-50 text-indigo-700 border-indigo-200",
};

function toMin(value: number) {
  if (value >= 60) {
    const h = Math.floor(value / 60);
    const m = value % 60;
    return `${h}h ${m}m`;
  }
  return `${value}m`;
}

export default function Home() {
  const [userId, setUserId] = useState("demo-user");
  const [profileName, setProfileName] = useState("Demo User");
  const [newProfileName, setNewProfileName] = useState("");

  const [vibes, setVibes] = useState<VibeOption[]>([]);
  const [vibe, setVibe] = useState("learn");
  const [device, setDevice] = useState("desktop");
  const [sessionMinutes, setSessionMinutes] = useState(35);

  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [rabbitHole, setRabbitHole] = useState<RabbitHoleResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = localStorage.getItem("omnistream_user_id");
    const storedName = localStorage.getItem("omnistream_user_name");
    if (stored) setUserId(stored);
    if (storedName) setProfileName(storedName);

    getVibes()
      .then((data) => setVibes(data.vibes))
      .catch(() => setError("Could not load vibe options. Is backend running?"));
  }, []);

  const loadExperience = async () => {
    setLoading(true);
    setError("");
    try {
      const [recData, resumeData] = await Promise.all([
        getRecommendations({
          user_id: userId,
          vibe,
          device,
          session_minutes: sessionMinutes,
          limit: 16,
        }),
        getResume(userId),
      ]);

      setRecommendation(recData);
      setResume(resumeData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not load recommendations.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadExperience();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, vibe, device, sessionMinutes]);

  const onInteraction = async (
    item: RecommendationCard,
    action: "view" | "click" | "like" | "skip" | "complete",
    completionRatio: number,
  ) => {
    setSaving(true);
    try {
      await logInteraction({
        user_id: userId,
        content_id: item.id,
        action,
        completion_ratio: completionRatio,
        time_spent_seconds: Math.round(item.duration_minutes * 60 * completionRatio),
        vibe,
        device,
        session_minutes: sessionMinutes,
      });
      await loadExperience();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save interaction");
    } finally {
      setSaving(false);
    }
  };

  const openRabbitHole = async (item: RecommendationCard) => {
    try {
      const hole = await getRabbitHole(item.id, userId, vibe);
      setRabbitHole(hole);
    } catch {
      setError("Could not generate rabbit-hole journey right now.");
    }
  };

  const createProfile = async () => {
    if (!newProfileName.trim()) return;
    try {
      const user = await bootstrapUser(newProfileName.trim());
      setUserId(user.id);
      setProfileName(user.name);
      localStorage.setItem("omnistream_user_id", user.id);
      localStorage.setItem("omnistream_user_name", user.name);
      setNewProfileName("");
      setRabbitHole(null);
    } catch {
      setError("Could not create profile.");
    }
  };

  const vibeObjective = useMemo(() => {
    const current = vibes.find((v) => v.id === vibe);
    return current?.objective || "Balanced cross-domain discovery";
  }, [vibes, vibe]);

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 md:px-8">
      <section className="soft-card fade-up rounded-3xl p-6 md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="mb-2 inline-flex rounded-full border border-teal-700/20 bg-teal-50 px-3 py-1 text-xs font-semibold tracking-wide text-teal-700">
              OmniStream AI
            </p>
            <h1 className="text-3xl font-bold md:text-5xl">Your AI content decision assistant</h1>
            <p className="mt-3 max-w-3xl text-sm text-slate-700 md:text-base">
              Not just recommendations. Context-aware, vibe-driven, cross-domain bundles with transparent reasoning.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white/80 p-4 text-sm">
            <p className="font-semibold">Active profile: {profileName}</p>
            <p className="text-xs text-slate-600">ID: {userId}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="soft-card rounded-3xl p-5">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Your vibe today</p>
          <div className="flex flex-wrap gap-2">
            {vibes.map((option) => (
              <button
                key={option.id}
                onClick={() => setVibe(option.id)}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  vibe === option.id
                    ? "border-teal-700 bg-teal-700 text-white"
                    : "border-slate-300 bg-white text-slate-700 hover:border-slate-500"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
          <p className="mt-3 text-sm text-slate-600">{vibeObjective}</p>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="text-sm">
              <span className="mb-1 block text-xs font-semibold uppercase text-slate-500">Device</span>
              <select
                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2"
                value={device}
                onChange={(e) => setDevice(e.target.value)}
              >
                {DEVICES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm md:col-span-2">
              <span className="mb-1 block text-xs font-semibold uppercase text-slate-500">
                Session duration: {sessionMinutes} min
              </span>
              <input
                type="range"
                min={10}
                max={120}
                step={5}
                value={sessionMinutes}
                onChange={(e) => setSessionMinutes(Number(e.target.value))}
                className="w-full"
              />
            </label>
          </div>
        </div>

        <div className="soft-card rounded-3xl p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">New profile</p>
          <p className="mb-3 mt-1 text-sm text-slate-600">Create your own profile for personalized memory graph.</p>
          <div className="flex gap-2">
            <input
              value={newProfileName}
              onChange={(e) => setNewProfileName(e.target.value)}
              placeholder="Your name"
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              onClick={createProfile}
              className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white"
            >
              Create
            </button>
          </div>
        </div>
      </section>

      {error ? (
        <section className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</section>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="soft-card rounded-3xl p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-bold">For You</h2>
            <button
              onClick={() => void loadExperience()}
              className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-wide"
            >
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {(recommendation?.recommendations || []).map((item) => (
              <article key={item.id} className="fade-up rounded-2xl border border-slate-200 bg-white p-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${DOMAIN_STYLES[item.domain]}`}>
                    {item.domain}
                  </span>
                  <span className="text-xs text-slate-500">{toMin(Math.round(item.duration_minutes))}</span>
                </div>
                <h3 className="text-base font-semibold">{item.title}</h3>
                <p className="mt-1 line-clamp-2 text-sm text-slate-600">{item.description}</p>
                <p className="mt-2 text-xs text-slate-700">{item.explanation}</p>

                <div className="mt-3 flex flex-wrap gap-2 text-xs">
                  <button
                    onClick={() => void onInteraction(item, "like", 0.8)}
                    disabled={saving}
                    className="rounded-lg border border-slate-300 px-2 py-1"
                  >
                    Like
                  </button>
                  <button
                    onClick={() => void onInteraction(item, "complete", 1)}
                    disabled={saving}
                    className="rounded-lg border border-slate-300 px-2 py-1"
                  >
                    Mark complete
                  </button>
                  <button
                    onClick={() => void openRabbitHole(item)}
                    className="rounded-lg border border-teal-300 bg-teal-50 px-2 py-1 text-teal-700"
                  >
                    Dive deeper
                  </button>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg border border-slate-300 px-2 py-1"
                  >
                    Open source
                  </a>
                </div>
              </article>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <section className="soft-card rounded-3xl p-5">
            <h2 className="text-lg font-bold">Context Engine</h2>
            <p className="mt-2 text-sm text-slate-700">{recommendation?.context.objective}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
              <div className="rounded-xl border border-slate-200 bg-white p-2">
                <p className="font-semibold">Time Segment</p>
                <p>{recommendation?.context.time_segment || "-"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-2">
                <p className="font-semibold">Momentum</p>
                <p>{recommendation?.insights.momentum_label || "-"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-2">
                <p className="font-semibold">Top Tags</p>
                <p>{(recommendation?.insights.top_tags || []).slice(0, 2).join(", ") || "-"}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-2">
                <p className="font-semibold">Curiosity</p>
                <p>{recommendation ? `${Math.round(recommendation.insights.curiosity_score * 100)}%` : "-"}</p>
              </div>
            </div>
          </section>

          <section className="soft-card rounded-3xl p-5">
            <h2 className="text-lg font-bold">Continue Exploring</h2>
            <div className="mt-3 space-y-2">
              {(resume?.items || []).slice(0, 4).map((item) => (
                <div key={item.content.id} className="rounded-xl border border-slate-200 bg-white p-3">
                  <p className="text-sm font-semibold">{item.content.title}</p>
                  <p className="text-xs text-slate-600">{Math.round(item.completion_ratio * 100)}% completed</p>
                </div>
              ))}
              {!resume?.items.length ? <p className="text-sm text-slate-600">No resume items yet.</p> : null}
            </div>
          </section>
        </div>
      </section>

      <section className="soft-card rounded-3xl p-5">
        <h2 className="text-xl font-bold">Cross-Domain Bundles</h2>
        <p className="mt-1 text-sm text-slate-600">
          This is your winning feature: not single recommendations, but curated action packs.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {(recommendation?.bundles || []).map((bundle) => (
            <article key={bundle.name} className="rounded-2xl border border-slate-200 bg-white p-4">
              <h3 className="text-base font-semibold">{bundle.name}</h3>
              <p className="mt-1 text-xs text-slate-600">{bundle.explanation}</p>
              <p className="mt-1 text-xs font-semibold text-slate-700">{toMin(bundle.expected_minutes)}</p>
              <ul className="mt-3 space-y-1 text-sm text-slate-700">
                {bundle.items.map((item) => (
                  <li key={item.id}>
                    <span className="font-semibold">{item.domain}:</span> {item.title}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      {rabbitHole ? (
        <section className="soft-card rounded-3xl p-5">
          <h2 className="text-xl font-bold">Rabbit Hole Journey</h2>
          <p className="mt-1 text-sm text-slate-600">Seed: {rabbitHole.seed.title}</p>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            {rabbitHole.journey.map((item) => (
              <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-3">
                <p className="text-xs uppercase tracking-wide text-slate-500">{item.domain}</p>
                <h3 className="mt-1 text-sm font-semibold">{item.title}</h3>
                <p className="mt-1 text-xs text-slate-600 line-clamp-3">{item.explanation}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </main>
  );
}
