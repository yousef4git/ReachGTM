"use client";

import { type ReactNode } from "react";
import { Sparkles, FileText } from "lucide-react";
import type { ChatMessage } from "@/store/useChatStore";

export const SUGGESTIONS = [
  "Who is our ICP and where do they hang out?",
  "Build me a battlecard against our top competitor.",
  "Draft 3 cold-email angles grounded in our positioning.",
  "What's the strongest proof point in our knowledge base?",
];

/**
 * Lightweight markdown-ish renderer for the streamed answer:
 * - `#`/`##`/`###` headings → styled heading line
 * - `- ` / `* ` bullets → hanging bullet
 * - `1.` ordered items → kept inline
 * - inline `**bold**` and `[n]` citation chips
 */
export function RichText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const heading = line.match(/^(#{1,3})\s+(.*)$/);
        if (heading) {
          return (
            <span
              key={i}
              className="mt-3 block text-[0.8125rem] font-semibold uppercase tracking-[0.04em] text-ink"
            >
              {renderInline(heading[2])}
            </span>
          );
        }
        const bullet = line.match(/^\s*[-*]\s+(.*)$/);
        if (bullet) {
          return (
            <span key={i} className="flex gap-2">
              <span className="mt-[0.6em] h-1 w-1 shrink-0 rounded-full bg-flare-600" />
              <span>{renderInline(bullet[1])}</span>
            </span>
          );
        }
        return (
          <span key={i} className="block">
            {renderInline(line)}
          </span>
        );
      })}
    </>
  );
}

function renderInline(line: string): ReactNode[] {
  const out: ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\[\d+\])/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = regex.exec(line)) !== null) {
    if (m.index > last) out.push(line.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith("**")) {
      out.push(
        <strong key={key++} className="font-semibold text-ink">
          {tok.slice(2, -2)}
        </strong>
      );
    } else {
      out.push(
        <sup
          key={key++}
          className="mono ml-0.5 rounded-[4px] bg-flare-50 px-1 text-[0.6rem] font-semibold text-flare-600"
        >
          {tok.slice(1, -1)}
        </sup>
      );
    }
    last = m.index + tok.length;
  }
  if (last < line.length) out.push(line.slice(last));
  return out;
}

export function Dot({ delay = "0s" }: { delay?: string }) {
  return (
    <span
      className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-faint"
      style={{ animationDelay: delay }}
    />
  );
}

export function AssistantMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="animate-rise">
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-ink text-canvas">
          <Sparkles className="h-3.5 w-3.5" strokeWidth={2} />
        </span>
        <span className="eyebrow !mb-0">Strategist</span>
      </div>

      <div className="mt-3 border-l-2 border-flare-600/70 pl-4">
        <div className="space-y-1 text-[0.95rem] leading-relaxed text-ink">
          {message.content ? (
            <RichText text={message.content} />
          ) : (
            <span className="inline-flex gap-1">
              <Dot /> <Dot delay="0.15s" /> <Dot delay="0.3s" />
            </span>
          )}
          {message.streaming && message.content && (
            <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-flare-600" />
          )}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            <span className="eyebrow !mb-0 !text-ink-faint">Grounded in</span>
            {message.sources.map((s, i) => (
              <span key={i} className="chip chip-ink gap-1" title={`${s.doc_type} · ${s.similarity}`}>
                <FileText className="h-3 w-3" />
                <span className="mono text-[0.625rem] text-flare-600">[{i + 1}]</span>
                {s.filename}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-end animate-rise">
      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-[0.9375rem] leading-relaxed text-canvas shadow-sm">
        {content}
      </div>
    </div>
  );
}
