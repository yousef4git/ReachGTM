"use client";

import { useState } from "react";
import type { ContentAsset } from "@/types";
import { ContentType, ValidationStatus } from "@/types";
import { cn } from "@/lib/utils";
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Trash2,
  FileText,
  MessageCircle,
  Newspaper,
  Megaphone,
} from "lucide-react";

interface ContentCardProps {
  asset: ContentAsset;
  onDelete?: (id: string) => void;
  className?: string;
}

const typeConfig: Record<ContentType, { label: string; icon: React.ReactNode }> = {
  [ContentType.COLD_EMAIL]: { label: "Cold Email", icon: <FileText className="h-3.5 w-3.5" /> },
  [ContentType.LINKEDIN_POST]: { label: "LinkedIn Post", icon: <MessageCircle className="h-3.5 w-3.5" /> },
  [ContentType.BLOG_OUTLINE]: { label: "Blog Outline", icon: <Newspaper className="h-3.5 w-3.5" /> },
  [ContentType.AD_COPY]: { label: "Ad Copy", icon: <Megaphone className="h-3.5 w-3.5" /> },
};

const statusChip: Record<string, string> = {
  [ValidationStatus.PENDING]: "chip-ink",
  [ValidationStatus.APPROVED]: "chip-success",
  [ValidationStatus.REJECTED]: "chip-danger",
  [ValidationStatus.REVISED]: "chip-warn",
};

const statusLabel: Record<string, string> = {
  [ValidationStatus.PENDING]: "Pending",
  [ValidationStatus.APPROVED]: "Approved",
  [ValidationStatus.REJECTED]: "Rejected",
  [ValidationStatus.REVISED]: "Revised",
};

export function ContentCard({ asset, onDelete, className }: ContentCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const config = typeConfig[asset.type] ?? typeConfig[ContentType.COLD_EMAIL];

  const handleCopy = async () => {
    await navigator.clipboard.writeText(asset.body);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("card lift flex flex-col", className)}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-hairline px-5 py-3.5">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="chip chip-ink">
            {config.icon}
            {config.label}
          </span>
          <span className={cn("chip", statusChip[asset.validation_status] ?? "chip-ink")}>
            {statusLabel[asset.validation_status] ?? "Pending"}
          </span>
        </div>
        <div className="flex items-center gap-0.5">
          <button
            onClick={handleCopy}
            title="Copy to clipboard"
            className="rounded-md p-1.5 text-ink-faint transition-colors hover:bg-sunken hover:text-ink"
          >
            {copied ? (
              <Check className="h-4 w-4 text-success" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </button>
          {onDelete && (
            <button
              onClick={() => onDelete(asset.id)}
              title="Delete"
              className="rounded-md p-1.5 text-ink-faint transition-colors hover:bg-danger-tint hover:text-danger"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 px-5 py-4">
        <h3 className="text-[0.9375rem] font-semibold leading-snug text-ink">
          {asset.title}
        </h3>
        <div className="relative mt-2">
          <pre
            className={cn(
              "whitespace-pre-wrap font-sans text-[0.8125rem] leading-relaxed text-ink-muted",
              !expanded && "line-clamp-4"
            )}
          >
            {asset.body}
          </pre>
          {asset.body.length > 300 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1.5 inline-flex items-center gap-1 text-[0.75rem] font-semibold text-flare-700 hover:text-flare-800"
            >
              {expanded ? (
                <>
                  Show less <ChevronUp className="h-3.5 w-3.5" />
                </>
              ) : (
                <>
                  Show more <ChevronDown className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-hairline px-5 py-3">
        <p className="mono text-[0.6875rem] text-ink-faint">
          {asset.target_icp && <>{asset.target_icp} · </>}
          {new Date(asset.created_at).toLocaleDateString()}
        </p>
        {asset.brand_alignment_score !== null &&
          asset.brand_alignment_score !== undefined && (
            <span
              className={cn(
                "mono text-[0.6875rem] font-semibold",
                asset.brand_alignment_score >= 0.7 ? "text-success" : "text-warn"
              )}
            >
              {Math.round(asset.brand_alignment_score * 100)}% on-brand
            </span>
          )}
      </div>
    </div>
  );
}
