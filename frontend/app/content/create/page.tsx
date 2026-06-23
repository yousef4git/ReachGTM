"use client";

import { useState, useCallback, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useGenerateContent } from "@/hooks/useContent";
import { useStore } from "@/store/useStore";
import { ContentType } from "@/types";
import type { ContentAsset } from "@/types";
import { ContentCard } from "@/components/content/ContentCard";
import {
  ArrowLeft,
  Sparkles,
  Loader2,
  CheckCircle,
  AlertCircle,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";

const CONTENT_TYPE_OPTIONS: { value: ContentType; label: string; description: string }[] = [
  { value: ContentType.COLD_EMAIL, label: "Cold Email", description: "Pattern-interrupt sales emails" },
  { value: ContentType.LINKEDIN_POST, label: "LinkedIn Post", description: "Scroll-stopping social content" },
  { value: ContentType.BLOG_OUTLINE, label: "Blog Outline", description: "SEO-friendly article structure" },
  { value: ContentType.AD_COPY, label: "Ad Copy", description: "Paid ads with strong CTAs" },
];

const COUNT_OPTIONS = [1, 3, 5, 10];

type Stage = "form" | "generating" | "result" | "error";

export default function CreateContentPage() {
  const router = useRouter();
  const addContentAsset = useStore((s) => s.addContentAsset);
  const { mutateAsync: generate, isPending: isGenerating } = useGenerateContent();

  const [phase, setPhase] = useState<Stage>("form");
  const [selectedTypes, setSelectedTypes] = useState<ContentType[]>([
    ContentType.COLD_EMAIL,
    ContentType.LINKEDIN_POST,
  ]);
  const [countPerType, setCountPerType] = useState(3);
  const [strategyId, setStrategyId] = useState("");
  const [generatedAssets, setGeneratedAssets] = useState<ContentAsset[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleType = (type: ContentType) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      setErrorMsg(null);

      if (selectedTypes.length === 0) {
        setErrorMsg("Select at least one content type.");
        return;
      }

      setPhase("generating");

      try {
        const result = await generate({
          strategy_id: strategyId.trim() || undefined,
          content_types: selectedTypes,
          count_per_type: countPerType,
        });

        const assets = result.content_assets ?? [];
        assets.forEach((a) => addContentAsset(a));
        setGeneratedAssets(assets);
        setPhase("result");
      } catch (err) {
        setPhase("error");
        setErrorMsg(err instanceof Error ? err.message : "Generation failed");
      }
    },
    [selectedTypes, countPerType, strategyId, generate, addContentAsset]
  );

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      <Link
        href="/content"
        className="mb-7 inline-flex items-center gap-1.5 text-[0.8125rem] font-medium text-ink-muted transition-colors hover:text-ink"
      >
        <ArrowLeft className="h-4 w-4" />
        Content library
      </Link>

      <header className="animate-rise mb-9">
        <p className="eyebrow">Create</p>
        <h1 className="display mt-2.5 text-[2.5rem] font-medium leading-tight text-ink">
          New content assets
        </h1>
        <p className="mt-2 text-[0.9375rem] text-ink-muted">
          Generate on-brand assets grounded in your GTM strategy context.
        </p>
      </header>

      {/* FORM PHASE */}
      {phase === "form" && (
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Content Types */}
          <div className="card p-6 sm:p-7">
            <h2 className="text-[0.9375rem] font-semibold text-ink">Content types</h2>
            <p className="mt-1 text-[0.8125rem] text-ink-muted">
              Pick what you want the agents to write.
            </p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {CONTENT_TYPE_OPTIONS.map((opt) => {
                const selected = selectedTypes.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleType(opt.value)}
                    className={cn(
                      "group flex items-start gap-3 rounded-lg border p-4 text-left transition-colors",
                      selected
                        ? "border-flare-600 bg-flare-50"
                        : "border-hairline-strong hover:border-ink-faint"
                    )}
                  >
                    <span
                      className={cn(
                        "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors",
                        selected
                          ? "border-flare-600 bg-flare-600 text-white"
                          : "border-hairline-strong"
                      )}
                    >
                      {selected && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
                    </span>
                    <span>
                      <span
                        className={cn(
                          "block text-[0.875rem] font-semibold",
                          selected ? "text-flare-800" : "text-ink"
                        )}
                      >
                        {opt.label}
                      </span>
                      <span className="mt-0.5 block text-[0.75rem] text-ink-muted">
                        {opt.description}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Count Per Type */}
          <div className="card p-6 sm:p-7">
            <h2 className="text-[0.9375rem] font-semibold text-ink">Quantity</h2>
            <p className="mt-1 text-[0.8125rem] text-ink-muted">
              How many pieces of each selected type?
            </p>
            <div className="mt-4 flex gap-2">
              {COUNT_OPTIONS.map((count) => (
                <button
                  key={count}
                  type="button"
                  onClick={() => setCountPerType(count)}
                  className={cn(
                    "mono w-14 rounded-md border py-2.5 text-[0.875rem] font-semibold transition-colors",
                    countPerType === count
                      ? "border-flare-600 bg-flare-50 text-flare-700"
                      : "border-hairline-strong text-ink-muted hover:border-ink-faint hover:text-ink"
                  )}
                >
                  {count}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy (Optional) */}
          <div className="card p-6 sm:p-7">
            <h2 className="text-[0.9375rem] font-semibold text-ink">
              Strategy context{" "}
              <span className="text-[0.8125rem] font-normal text-ink-faint">
                — optional
              </span>
            </h2>
            <p className="mt-1 mb-4 text-[0.8125rem] text-ink-muted">
              Link a strategy to tailor content to its ICP and positioning.
            </p>
            <input
              type="text"
              value={strategyId}
              onChange={(e) => setStrategyId(e.target.value)}
              placeholder="Paste a strategy ID, or leave blank"
              className="field mono"
            />
          </div>

          {errorMsg && (
            <div className="alert alert-danger">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            disabled={isGenerating || selectedTypes.length === 0}
            className="btn btn-flare w-full py-3.5 text-[0.9375rem]"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Generating…
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Generate{" "}
                {selectedTypes.length > 1
                  ? `${selectedTypes.length} content types`
                  : "content"}
              </>
            )}
          </button>
        </form>
      )}

      {/* GENERATING PHASE */}
      {phase === "generating" && (
        <div className="card p-6 sm:p-7">
          <div className="flex items-center gap-3">
            <span className="signal-pulse flex h-9 w-9 items-center justify-center rounded-full bg-flare-600">
              <Loader2 className="h-4 w-4 animate-spin text-white" />
            </span>
            <div>
              <p className="font-semibold text-ink">Agents writing content…</p>
              <p className="text-[0.8125rem] text-ink-muted">
                {countPerType} pieces each for{" "}
                {selectedTypes.map((t) => t.replace(/_/g, " ")).join(", ")}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* RESULT PHASE */}
      {phase === "result" && (
        <div className="space-y-5">
          <div className="alert alert-success items-center">
            <CheckCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Content generated</p>
              <p className="text-[0.8125rem] opacity-80">
                {generatedAssets.length} assets created for{" "}
                {selectedTypes.map((t) => t.replace(/_/g, " ")).join(", ")}
              </p>
            </div>
          </div>

          {generatedAssets.length > 0 ? (
            <div className="stagger grid gap-4 sm:grid-cols-2">
              {generatedAssets.map((asset) => (
                <ContentCard key={asset.id} asset={asset} />
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-hairline-strong bg-surface p-8 text-center text-[0.875rem] text-ink-faint">
              No assets were returned. Generation may still be running on the
              backend.
            </div>
          )}

          <div className="flex gap-3">
            <button onClick={() => setPhase("form")} className="btn btn-secondary">
              Generate more
            </button>
            <button
              onClick={() => router.push("/content")}
              className="btn btn-primary"
            >
              View library
            </button>
          </div>
        </div>
      )}

      {/* ERROR PHASE */}
      {phase === "error" && (
        <div className="space-y-5">
          <div className="alert alert-danger items-center">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Generation failed</p>
              <p className="text-[0.8125rem] opacity-80">
                {errorMsg || "An unexpected error occurred."}
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
