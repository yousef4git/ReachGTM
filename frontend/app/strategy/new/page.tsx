"use client";

import { useState, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useGenerateStrategy } from "@/hooks/useStrategy";
import { AgentProgress } from "@/components/agent/AgentProgress";
import { AgentEventFeed } from "@/components/agent/AgentEventFeed";
import { StrategyCard } from "@/components/strategy/StrategyCard";
import type { GTMStrategy } from "@/types";
import { ArrowRight, Sparkles, Loader2, CheckCircle, AlertCircle } from "lucide-react";

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
      // Fallback: check for any data in done event
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
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-3xl px-4 py-10">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Generate GTM Strategy</h1>
          <p className="mt-2 text-gray-500">
            Describe your company and let the AI agents research, strategize, and create content.
          </p>
        </div>

        {/* Form Phase */}
        {phase === "form" && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">Company Profile</h2>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Company Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text" required value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Acme Corp"
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Website</label>
                  <input
                    type="url" value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://acme.com"
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Industry <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text" required value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    placeholder="B2B SaaS, Fintech, Healthcare…"
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Stage</label>
                  <select
                    value={stage}
                    onChange={(e) => setStage(e.target.value as Stage)}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    {STAGE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Founded Year</label>
                  <input
                    type="number" min={1900} max={2030} value={foundedYear}
                    onChange={(e) => setFoundedYear(e.target.value)}
                    placeholder="2024"
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Company Description <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    required value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe what your company does, who you serve, and your key differentiators…"
                    rows={4}
                    className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {formError && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4" />
                {formError}
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting agents…
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate Strategy
                </>
              )}
            </button>
          </form>
        )}

        {/* Generating Phase */}
        {phase === "generating" && (
          <div className="space-y-6">
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h2 className="mb-2 text-lg font-semibold text-gray-900">
                Agents at work
              </h2>
              <p className="mb-6 text-sm text-gray-500">
                Running research → strategy → content → brand alignment
              </p>
              <AgentProgress events={events} />
            </div>

            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-700">Event Log</h3>
                <span className="text-xs text-gray-400">{events.length} events</span>
              </div>
              <AgentEventFeed events={events} />
            </div>

            <button
              onClick={stop}
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Result Phase */}
        {phase === "result" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-semibold text-green-800">Strategy generated successfully!</p>
                <p className="text-sm text-green-600">
                  4 agents ran in sequence, {events.length} events captured
                </p>
              </div>
            </div>

            {result ? (
              <StrategyCard strategy={result} className="border-green-200" />
            ) : (
              <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-400">
                Strategy data will appear here once the backend is wired.
              </div>
            )}

            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h3 className="mb-3 text-sm font-semibold text-gray-700">Event Log</h3>
              <AgentEventFeed events={events} />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => router.push("/strategy/new")}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Generate Another
              </button>
              <button
                onClick={() => router.push("/content/create")}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
              >
                Create Content Assets
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Error Phase */}
        {phase === "error" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">Generation failed</p>
                <p className="text-sm text-red-600">
                  {streamError || formError || "An unexpected error occurred."}
                </p>
              </div>
            </div>
            <button
              onClick={() => setPhase("form")}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
