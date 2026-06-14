"use client";

import { useState, useCallback, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useGenerateContent } from "@/hooks/useContent";
import { useStore } from "@/store/useStore";
import { ContentType } from "@/types";
import type { ContentAsset } from "@/types";
import { ContentCard } from "@/components/content/ContentCard";
import { ArrowLeft, Sparkles, Loader2, CheckCircle, AlertCircle } from "lucide-react";
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
  const [selectedTypes, setSelectedTypes] = useState<ContentType[]>([ContentType.COLD_EMAIL, ContentType.LINKEDIN_POST]);
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
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-10">
        {/* Back link */}
        <Link
          href="/content"
          className="mb-6 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Content Library
        </Link>

        <h1 className="mb-2 text-3xl font-bold text-gray-900">Create Content</h1>
        <p className="mb-8 text-sm text-gray-500">
          Generate AI-powered content assets using your GTM strategy context.
        </p>

        {/* FORM PHASE */}
        {phase === "form" && (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Content Types */}
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">Content Types</h2>
              <p className="mb-4 text-sm text-gray-500">
                Select the types of content you want to generate.
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                {CONTENT_TYPE_OPTIONS.map((opt) => {
                  const selected = selectedTypes.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleType(opt.value)}
                      className={cn(
                        "flex flex-col items-start rounded-lg border p-4 text-left transition-colors",
                        selected
                          ? "border-blue-300 bg-blue-50 ring-1 ring-blue-200"
                          : "border-gray-200 bg-white hover:border-gray-300"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "flex h-5 w-5 items-center justify-center rounded border",
                          selected ? "border-blue-600 bg-blue-600" : "border-gray-300"
                        )}>
                          {selected && <CheckCircle className="h-4 w-4 text-white" />}
                        </div>
                        <span className={cn(
                          "text-sm font-medium",
                          selected ? "text-blue-700" : "text-gray-700"
                        )}>
                          {opt.label}
                        </span>
                      </div>
                      <p className="mt-1 pl-7 text-xs text-gray-400">{opt.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Count Per Type */}
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">Quantity</h2>
              <p className="mb-4 text-sm text-gray-500">
                How many pieces of each selected type?
              </p>
              <div className="flex gap-2">
                {COUNT_OPTIONS.map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setCountPerType(count)}
                    className={cn(
                      "rounded-lg border px-5 py-2 text-sm font-medium transition-colors",
                      countPerType === count
                        ? "border-blue-300 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    )}
                  >
                    {count}
                  </button>
                ))}
              </div>
            </div>

            {/* Strategy (Optional) */}
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Strategy Context <span className="text-sm font-normal text-gray-400">(optional)</span>
              </h2>
              <p className="mb-4 text-sm text-gray-500">
                Link to a specific strategy to tailor content to its ICP and positioning.
              </p>
              <input
                type="text"
                value={strategyId}
                onChange={(e) => setStrategyId(e.target.value)}
                placeholder="Paste a strategy ID, or leave blank for generic generation"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {errorMsg && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {errorMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating || selectedTypes.length === 0}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isGenerating ? (
                <><Loader2 className="h-4 w-4 animate-spin" /> Generating…</>
              ) : (
                <><Sparkles className="h-4 w-4" /> Generate {selectedTypes.length > 1 ? `${selectedTypes.length} Content Types` : "Content"}</>
              )}
            </button>
          </form>
        )}

        {/* GENERATING PHASE */}
        {phase === "generating" && (
          <div className="space-y-6">
            <div className="rounded-xl border bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                <div>
                  <p className="font-semibold text-gray-900">Agents generating content…</p>
                  <p className="text-sm text-gray-500">
                    Creating {countPerType} pieces each for{" "}
                    {selectedTypes.map((t) => t.replace(/_/g, " ")).join(", ")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RESULT PHASE */}
        {phase === "result" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <p className="font-semibold text-green-800">Content generated successfully!</p>
                <p className="text-sm text-green-600">
                  {generatedAssets.length} assets created for{" "}
                  {selectedTypes.map((t) => t.replace(/_/g, " ")).join(", ")}
                </p>
              </div>
            </div>

            {generatedAssets.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2">
                {generatedAssets.map((asset) => (
                  <ContentCard key={asset.id} asset={asset} />
                ))}
              </div>
            )}

            {generatedAssets.length === 0 && (
              <div className="rounded-xl border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-400">
                No assets were returned. The generation may still be running on the backend.
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setPhase("form")}
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                Generate More
              </button>
              <button
                onClick={() => router.push("/content")}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
              >
                View Library
              </button>
            </div>
          </div>
        )}

        {/* ERROR PHASE */}
        {phase === "error" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">Generation failed</p>
                <p className="text-sm text-red-600">{errorMsg || "An unexpected error occurred."}</p>
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
