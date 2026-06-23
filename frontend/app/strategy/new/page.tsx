"use client";

import { useState, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useGenerateStrategy } from "@/hooks/useStrategy";
import { AgentProgress } from "@/components/agent/AgentProgress";
import { AgentEventFeed } from "@/components/agent/AgentEventFeed";
import { StrategyCard } from "@/components/strategy/StrategyCard";
import type { GTMStrategy } from "@/types";
import { cn } from "@/lib/utils";
import {
  ArrowRight,
  Compass,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

type Stage = "seed" | "series_a" | "series_b" | "growth";

const STAGE_OPTIONS: { value: Stage; label: string }[] = [
  { value: "seed", label: "Seed" },
  { value: "series_a", label: "Series A" },
  { value: "series_b", label: "Series B" },
  { value: "growth", label: "Growth" },
];

export default function NewStrategyPage() {
  const router = useRouter();
  const { events, isStreaming, error: streamError, start, stop } = useAgentStream();
  const { mutateAsync: generate, isPending: isGenerating } = useGenerateStrategy();

  const [phase, setPhase] = useState<"form" | "generating" | "result" | "error">("form");
  const [result, setResult] = useState<GTMStrategy | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [industry, setIndustry] = useState("");
  const [stage, setStage] = useState<Stage>("seed");
  const [description, setDescription] = useState("");
  const [foundedYear, setFoundedYear] = useState("");

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setFormError(null);

      if (!name.trim() || !industry.trim() || !description.trim()) {
        setFormError("Company name, industry, and description are required.");
        return;
      }

      setPhase("generating");

      try {
        const profile = {
          name: name.trim(),
          website: website.trim() || undefined,
          industry: industry.trim(),
          stage,
          description: description.trim(),
          founded_year: foundedYear ? parseInt(foundedYear, 10) : undefined,
        };

        const resp = await generate(profile);
        const goal = `Build a go-to-market strategy for ${profile.name}, a ${stage}-stage ${profile.industry} company. ${profile.description}`;
        start(resp.session_id, goal);
      } catch (err) {
        setPhase("error");
        setFormError(err instanceof Error ? err.message : "Failed to start generation");
      }
    },
    [name, website, industry, stage, description, foundedYear, generate, start]
  );

  // Check if generation completed
  const isDone = events.some((e) => e.event === "done");
  const hasError = events.some((e) => e.event === "error");

  // When done, try to extract the strategy result from events
  if (isDone && phase === "generating") {
    const outputEvent = events.find((e) => e.event === "agent_output" && e.agent === "strategy");
    if (outputEvent?.data) {
      setResult(outputEvent.data as GTMStrategy);
      setPhase("result");
    } else {
      const doneEvent = events.find((e) => e.event === "done");
      if (doneEvent?.data) {
        setResult(doneEvent.data as GTMStrategy);
        setPhase("result");
      } else {
        setPhase("result");
      }
    }
  }

  if (hasError && phase === "generating") {
    setPhase("error");
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      {/* Header */}
      <header className="animate-rise mb-10">
        <p className="eyebrow">New strategy · Step 01</p>
        <h1 className="display mt-3 text-[2.5rem] font-medium leading-tight text-ink">
          Aim the agents.
        </h1>
        <p className="mt-2.5 max-w-xl text-[1rem] leading-relaxed text-ink-muted">
          Describe your company. Four specialist agents will research, strategize,
          and draft content — streaming their work live.
        </p>
      </header>

      {/* Form Phase */}
      {phase === "form" && (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="card p-6 sm:p-7">
            <h2 className="text-[0.9375rem] font-semibold text-ink">
              Company profile
            </h2>
            <div className="rule mt-4 mb-5" />

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="field-label">
                  Company name <span className="text-flare-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Acme Corp"
                  className="field"
                />
              </div>

              <div>
                <label className="field-label">Website</label>
                <input
                  type="url"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  placeholder="https://acme.com"
                  className="field"
                />
              </div>

              <div>
                <label className="field-label">
                  Industry <span className="text-flare-600">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  placeholder="B2B SaaS, Fintech, Healthcare…"
                  className="field"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="field-label">Stage</label>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {STAGE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setStage(opt.value)}
                      className={cn(
                        "rounded-md border px-3 py-2.5 text-[0.8125rem] font-semibold transition-colors",
                        stage === opt.value
                          ? "border-flare-600 bg-flare-50 text-flare-700"
                          : "border-hairline-strong text-ink-muted hover:border-ink-faint hover:text-ink"
                      )}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="field-label">Founded year</label>
                <input
                  type="number"
                  min={1900}
                  max={2030}
                  value={foundedYear}
                  onChange={(e) => setFoundedYear(e.target.value)}
                  placeholder="2024"
                  className="field"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="field-label">
                  Company description <span className="text-flare-600">*</span>
                </label>
                <textarea
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What you do, who you serve, and your key differentiators…"
                  rows={4}
                  className="field resize-none"
                />
              </div>
            </div>
          </div>

          {formError && (
            <div className="alert alert-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              {formError}
            </div>
          )}

          <button
            type="submit"
            disabled={isGenerating}
            className="btn btn-flare w-full py-3.5 text-[0.9375rem]"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting agents…
              </>
            ) : (
              <>
                <Compass className="h-4 w-4" />
                Generate strategy
              </>
            )}
          </button>
        </form>
      )}

      {/* Generating Phase */}
      {phase === "generating" && (
        <div className="space-y-5">
          <div className="card p-6 sm:p-7">
            <div className="flex items-center gap-2">
              <span className="signal-pulse h-2 w-2 rounded-full bg-flare-600" />
              <h2 className="eyebrow !text-flare-700">Agents at work</h2>
            </div>
            <p className="mt-3 mb-6 text-[0.875rem] text-ink-muted">
              Running research → strategy → content → brand alignment.
            </p>
            <AgentProgress events={events} />
          </div>

          <div className="card p-6 sm:p-7">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="eyebrow">Event log</h3>
              <span className="mono text-[0.6875rem] text-ink-faint">
                {events.length} events
              </span>
            </div>
            <AgentEventFeed events={events} />
          </div>

          <button onClick={stop} className="btn btn-secondary w-full">
            Cancel
          </button>
        </div>
      )}

      {/* Result Phase */}
      {phase === "result" && (
        <div className="space-y-5">
          <div className="alert alert-success items-center">
            <CheckCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Strategy generated</p>
              <p className="text-[0.8125rem] opacity-80">
                4 agents ran in sequence · {events.length} events captured.
              </p>
            </div>
          </div>

          {result ? (
            <StrategyCard strategy={result} />
          ) : (
            <div className="rounded-xl border border-dashed border-hairline-strong bg-surface p-8 text-center text-[0.875rem] text-ink-faint">
              Strategy data will appear here once the backend is wired.
            </div>
          )}

          <div className="card p-6 sm:p-7">
            <h3 className="eyebrow mb-3">Event log</h3>
            <AgentEventFeed events={events} />
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => router.push("/strategy/new")}
              className="btn btn-secondary"
            >
              Generate another
            </button>
            <button
              onClick={() => router.push("/content/create")}
              className="btn btn-primary"
            >
              Create content assets
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Error Phase */}
      {phase === "error" && (
        <div className="space-y-5">
          <div className="alert alert-danger items-center">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Generation failed</p>
              <p className="text-[0.8125rem] opacity-80">
                {streamError || formError || "An unexpected error occurred."}
              </p>
            </div>
          </div>
          <button onClick={() => setPhase("form")} className="btn btn-flare w-full">
            Try again
          </button>
        </div>
      )}
    </main>
  );
}
