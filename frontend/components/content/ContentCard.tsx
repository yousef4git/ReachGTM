"use client";

import { useState } from "react";
import type { ContentAsset } from "@/types";
import { ContentType, ValidationStatus } from "@/types";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Copy, Check, Trash2, FileText, MessageCircle, Newspaper, Megaphone } from "lucide-react";

interface ContentCardProps {
  asset: ContentAsset;
  onDelete?: (id: string) => void;
  className?: string;
}

const typeConfig: Record<ContentType, { label: string; icon: React.ReactNode; color: string }> = {
  [ContentType.COLD_EMAIL]: {
    label: "Cold Email",
    icon: <FileText className="h-4 w-4" />,
    color: "bg-blue-50 text-blue-700 border-blue-200",
  },
  [ContentType.LINKEDIN_POST]: {
    label: "LinkedIn Post",
    icon: <MessageCircle className="h-4 w-4" />,
    color: "bg-sky-50 text-sky-700 border-sky-200",
  },
  [ContentType.BLOG_OUTLINE]: {
    label: "Blog Outline",
    icon: <Newspaper className="h-4 w-4" />,
    color: "bg-purple-50 text-purple-700 border-purple-200",
  },
  [ContentType.AD_COPY]: {
    label: "Ad Copy",
    icon: <Megaphone className="h-4 w-4" />,
    color: "bg-amber-50 text-amber-700 border-amber-200",
  },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  [ValidationStatus.PENDING]: { label: "Pending", color: "bg-gray-100 text-gray-600" },
  [ValidationStatus.APPROVED]: { label: "Approved", color: "bg-green-100 text-green-700" },
  [ValidationStatus.REJECTED]: { label: "Rejected", color: "bg-red-100 text-red-700" },
  [ValidationStatus.REVISED]: { label: "Revised", color: "bg-yellow-100 text-yellow-700" },
};

export function ContentCard({ asset, onDelete, className }: ContentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const config = typeConfig[asset.type] ?? typeConfig[ContentType.COLD_EMAIL];
  const statusCfg = statusConfig[asset.validation_status] ?? statusConfig[ValidationStatus.PENDING];

  const handleCopy = async () => {
    await navigator.clipboard.writeText(asset.body);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("rounded-xl border bg-white shadow-sm transition-shadow hover:shadow-md", className)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${config.color}`}>
            {config.icon}
            {config.label}
          </span>
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusCfg.color}`}>
            {statusCfg.label}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            title="Copy to clipboard"
            className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </button>
          {onDelete && (
            <button
              onClick={() => onDelete(asset.id)}
              title="Delete"
              className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-500"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="px-5 py-4">
        <h3 className="mb-2 text-sm font-semibold text-gray-900">{asset.title}</h3>
        <div className="relative">
          <pre className={`whitespace-pre-wrap text-sm leading-relaxed text-gray-600 ${expanded ? "" : "line-clamp-4"}`}>
            {asset.body}
          </pre>
          {asset.body.length > 300 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
            >
              {expanded ? (
                <>Show less <ChevronUp className="h-3 w-3" /></>
              ) : (
                <>Show more <ChevronDown className="h-3 w-3" /></>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-gray-100 px-5 py-3">
        <p className="text-xs text-gray-400">
          {asset.target_icp && <>ICP: {asset.target_icp} · </>}
          {new Date(asset.created_at).toLocaleDateString()}
        </p>
        {asset.brand_alignment_score !== null && asset.brand_alignment_score !== undefined && (
          <span className={`text-xs font-medium ${
            asset.brand_alignment_score >= 0.7 ? "text-green-600" : "text-amber-600"
          }`}>
            Score: {Math.round(asset.brand_alignment_score * 100)}%
          </span>
        )}
      </div>
    </div>
  );
}
