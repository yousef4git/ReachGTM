"use client";

import { useState, useCallback, useEffect, type FormEvent } from "react";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useGenerateStrategy } from "@/hooks/useStrategy";
import { AgentProgress } from "@/components/agent/AgentProgress";
import { AgentEventFeed } from "@/components/agent/AgentEventFeed";
import { StrategyResult } from "@/components/strategy/StrategyResult";
import { useStore } from "@/store/useStore";
import type { StrategyBundle, GTMStrategy, ContentAsset, ResearchHighlights } from "@/types";
import { cn } from "@/lib/utils";
import { Compass, Loader2, AlertCircle } from "lucide-react";

type Stage = "seed" | "series_a" | "series_b" | "growth";

const STAGE_OPTIONS: { value: Stage; label: string }[] = [
  { value: "seed", label: "Seed" },
  { value: "series_a", label: "Series A" },
  { value: "series_b", label: "Series B" },
  { value: "growth", label: "Growth" },
];

export default function NewStrategyPage() {
  const { events, error: streamError, start, stop } = useAgentStream();
  const { mutateAsync: generate, isPending: isGenerating } = useGenerateStrategy();
  const setStrategy = useStore((s) => s.setStrategy);
  const setContentAssets = useStore((s) => s.setContentAssets);

  const [phase, setPhase] = useState<"form" | "generating" | "result" | "error">("form");
  const [bundle, setBundle] = useState<StrategyBundle | null>(null);
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

  // `agent_complete` is terminal: useAgentStream closes the EventSource on it,
  // so the trailing `done` frame may never arrive — treat either as completion.
  const isDone = events.some((e) => e.event === "done" || e.event === "agent_complete");
  const hasError = events.some((e) => e.event === "error");

  // On completion: assemble the deliverable bundle from the stream, push it into
  // the shared store (so the Content library and dashboard see it), and switch
  // to the result view.
  useEffect(() => {
    if (phase !== "generating") return;
    if (hasError) {
      setPhase("error");
      return;
    }
    if (!isDone) return;

    const complete = events.find((e) => e.event === "agent_complete")?.data as
      | { gtm_strategy?: GTMStrategy; content_assets?: ContentAsset[]; research_report?: ResearchHighlights }
      | undefined;

    let next: StrategyBundle;
    if (complete && (complete.gtm_strategy || complete.content_assets?.length)) {
      next = {
        gtm_strategy: complete.gtm_strategy ?? null,
        content_assets: complete.content_assets ?? [],
        research_report: complete.research_report ?? null,
      };
    } else {
      // Fallback: stitch from individual agent_output frames.
      const strat = (events.find((e) => e.event === "agent_output" && e.agent === "strategy")?.data ?? null) as GTMStrategy | null;
      const contentFrames = events.filter((e) => e.event === "agent_output" && /content/.test(e.message ?? ""));
      const assets = (contentFrames.at(-1)?.data ?? []) as ContentAsset[];
      const research = (events.find((e) => e.event === "agent_output" && e.agent === "research")?.data ?? null) as ResearchHighlights | null;
      next = { gtm_strategy: strat, content_assets: assets, research_report: research };
    }

    setBundle(next);
    if (next.gtm_strategy) setStrategy(next.gtm_strategy);
    if (next.content_assets.length) setContentAssets(next.content_assets);
    setPhase("result");
  }, [isDone, hasError, phase, events, setStrategy, setContentAssets]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      {/* Header */}
      {phase !== "result" && (
        <header className="animate-rise mb-10">
          <p className="eyebrow">
            New strategy · {phase === "generating" ? "Working" : "Step 01"}
          </p>
          <h1 className="display mt-3 text-[2.5rem] font-medium leading-tight text-ink">
            {phase === "generating" ? "Agents on the case." : "Aim the agents."}
          </h1>
          <p className="mt-2.5 max-w-xl text-[1rem] leading-relaxed text-ink-muted">
            {phase === "generating"
              ? "Research, strategy, content, and brand alignment — streaming live below."
              : "Describe your company. Four specialist agents will research, strategize, and draft content — streaming their work live."}
          </p>
        </header>
      )}

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
      {phase === "result" && bundle && (
        <div className="space-y-6">
          <StrategyResult bundle={bundle} companyName={name || "Your company"} />

          <details className="card group p-6 sm:p-7">
            <summary className="flex cursor-pointer list-none items-center justify-between">
              <h3 className="eyebrow">Event log</h3>
              <span className="mono text-[0.6875rem] text-ink-faint group-open:hidden">
                {events.length} events · show
              </span>
              <span className="mono hidden text-[0.6875rem] text-ink-faint group-open:inline">
                hide
              </span>
            </summary>
            <div className="mt-4">
              <AgentEventFeed events={events} />
            </div>
          </details>
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
