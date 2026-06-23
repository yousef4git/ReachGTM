"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { ContentCard } from "@/components/content/ContentCard";
import { useContentList } from "@/hooks/useContent";
import { useStore } from "@/store/useStore";
import { ContentType } from "@/types";
import {
  Plus,
  FileText,
  MessageCircle,
  Newspaper,
  Megaphone,
  Loader2,
  AlertCircle,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ALL_TAB = "all";

const TABS: { value: string; label: string; icon: React.ReactNode }[] = [
  { value: ALL_TAB, label: "All", icon: <Layers className="h-4 w-4" /> },
  { value: ContentType.COLD_EMAIL, label: "Cold Email", icon: <FileText className="h-4 w-4" /> },
  { value: ContentType.LINKEDIN_POST, label: "LinkedIn", icon: <MessageCircle className="h-4 w-4" /> },
  { value: ContentType.BLOG_OUTLINE, label: "Blog", icon: <Newspaper className="h-4 w-4" /> },
  { value: ContentType.AD_COPY, label: "Ad Copy", icon: <Megaphone className="h-4 w-4" /> },
];

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState(ALL_TAB);
  const { data: assets, isLoading, error } = useContentList();
  const contentAssets = useStore((s) => s.contentAssets);
  const removeContentAsset = useStore((s) => s.removeContentAsset);

  const allAssets = assets ?? contentAssets;

  const filtered = useMemo(() => {
    if (activeTab === ALL_TAB) return allAssets;
    return allAssets.filter((a) => a.type === activeTab);
  }, [allAssets, activeTab]);

  const handleDelete = (id: string) => removeContentAsset(id);

  return (
    <main className="mx-auto max-w-5xl px-5 py-12 sm:px-8 sm:py-16">
      {/* Header */}
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div className="animate-rise">
          <p className="eyebrow">Library</p>
          <h1 className="display mt-2.5 text-[2.5rem] font-medium leading-tight text-ink">
            Content
          </h1>
          <p className="mt-2 text-[0.9375rem] text-ink-muted">
            Browse, review, and manage every generated asset.
          </p>
        </div>
        <Link href="/content/create" className="btn btn-flare">
          <Plus className="h-4 w-4" />
          Create content
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="mb-7 flex gap-1 overflow-x-auto rounded-xl border border-hairline bg-surface p-1.5 shadow-sm">
        {TABS.map((tab) => {
          const active = activeTab === tab.value;
          const count = tab.value === ALL_TAB
            ? allAssets.length
            : allAssets.filter((a) => a.type === tab.value).length;
          return (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                "flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-[0.8125rem] font-semibold transition-colors",
                active
                  ? "bg-ink text-canvas"
                  : "text-ink-muted hover:bg-sunken hover:text-ink"
              )}
            >
              {tab.icon}
              {tab.label}
              <span
                className={cn(
                  "mono rounded-full px-1.5 text-[0.625rem]",
                  active ? "bg-white/15 text-canvas" : "text-ink-faint"
                )}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-6 w-6 animate-spin text-flare-600" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="alert alert-danger mb-6">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">Could not load content</p>
            <p className="opacity-80">
              {error instanceof Error
                ? error.message
                : "Backend may be offline. Showing local assets."}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filtered.length === 0 && (
        <div className="rounded-2xl border border-dashed border-hairline-strong bg-surface p-14 text-center">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-sunken text-ink-faint">
            <FileText className="h-6 w-6" />
          </span>
          <h3 className="mt-4 text-[1.0625rem] font-semibold text-ink">
            {activeTab === ALL_TAB ? "No content yet" : "Nothing of this type"}
          </h3>
          <p className="mx-auto mt-1.5 max-w-sm text-[0.875rem] text-ink-muted">
            {activeTab === ALL_TAB
              ? "Generate your first content asset to get started."
              : "Switch tabs, or generate content of this type."}
          </p>
          <Link
            href="/content/create"
            className="btn btn-primary mx-auto mt-6"
          >
            <Plus className="h-4 w-4" />
            Create content
          </Link>
        </div>
      )}

      {/* Content Grid */}
      {filtered.length > 0 && (
        <div className="stagger grid gap-4 sm:grid-cols-2">
          {filtered.map((asset) => (
            <ContentCard key={asset.id} asset={asset} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </main>
  );
}
