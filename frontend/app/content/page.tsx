"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { ContentCard } from "@/components/content/ContentCard";
import { useContentList } from "@/hooks/useContent";
import { useStore } from "@/store/useStore";
import { ContentType } from "@/types";
import { Plus, FileText, MessageCircle, Newspaper, Megaphone, Loader2, AlertCircle, Layers } from "lucide-react";
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

  // Use server data if available, fall back to local store
  const allAssets = assets ?? contentAssets;

  const filtered = useMemo(() => {
    if (activeTab === ALL_TAB) return allAssets;
    return allAssets.filter((a) => a.type === activeTab);
  }, [allAssets, activeTab]);

  const handleDelete = (id: string) => {
    removeContentAsset(id);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-5xl px-4 py-10">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Content Library</h1>
            <p className="mt-1 text-sm text-gray-500">
              Browse, review, and manage your generated content assets.
            </p>
          </div>
          <Link
            href="/content/create"
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            Create Content
          </Link>
        </div>

        {/* Filter Tabs */}
        <div className="mb-6 flex gap-1.5 overflow-x-auto rounded-xl border bg-white p-1.5 shadow-sm">
          {TABS.map((tab) => (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeTab === tab.value
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-500 hover:bg-gray-100 hover:text-gray-700"
              )}
            >
              {tab.icon}
              {tab.label}
              {activeTab === tab.value && (
                <span className="ml-1 rounded-full bg-blue-200 px-1.5 py-0.5 text-xs text-blue-700">
                  {activeTab === ALL_TAB ? allAssets.length : filtered.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-5 py-4">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
            <div>
              <p className="text-sm font-medium text-red-800">Could not load content</p>
              <p className="text-sm text-red-600">
                {error instanceof Error ? error.message : "Backend may be offline. Showing local assets."}
              </p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && filtered.length === 0 && (
          <div className="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center">
            <FileText className="mx-auto mb-4 h-10 w-10 text-gray-300" />
            <h3 className="mb-1 text-lg font-semibold text-gray-900">
              {activeTab === ALL_TAB ? "No content yet" : "No content of this type"}
            </h3>
            <p className="mb-6 text-sm text-gray-500">
              {activeTab === ALL_TAB
                ? "Generate your first content asset to get started."
                : "Switch to a different tab or generate content of this type."}
            </p>
            <Link
              href="/content/create"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Create Content
            </Link>
          </div>
        )}

        {/* Content Grid */}
        {filtered.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {filtered.map((asset) => (
              <ContentCard
                key={asset.id}
                asset={asset}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
