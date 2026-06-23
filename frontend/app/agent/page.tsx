"use client";

import { useRef, useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import { Sparkles, ArrowUp, Library, Compass, FileStack, Brain, RotateCcw, AlertCircle } from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { AssistantMessage, UserMessage, SUGGESTIONS } from "@/components/chat/chatParts";

const GROUNDING_LEGEND = [
  { icon: Library, label: "Knowledge base" },
  { icon: Compass, label: "GTM strategy" },
  { icon: FileStack, label: "Content library" },
  { icon: Brain, label: "Company memory" },
];

export default function AgentPage() {
  const { messages, isStreaming, error, send, reset } = useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isStreaming) return;
    send(input);
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const empty = messages.length === 0;

  return (
    <div className="mx-auto flex h-[calc(100vh-4rem)] max-w-3xl flex-col px-5 sm:px-8">
      <header className="shrink-0 border-b border-hairline py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Assistant</p>
            <h1 className="display mt-2 text-[2rem] font-medium leading-tight text-ink">
              Strategy Desk
            </h1>
            <p className="mt-1.5 text-[0.9rem] text-ink-muted">
              Ask anything. Answers are grounded in everything your company has built.
            </p>
          </div>
          {!empty && (
            <button onClick={reset} className="btn btn-ghost shrink-0" title="New conversation">
              <RotateCcw className="h-4 w-4" />
              New
            </button>
          )}
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          {GROUNDING_LEGEND.map(({ icon: Icon, label }) => (
            <span key={label} className="flex items-center gap-1.5 text-[0.75rem] text-ink-faint">
              <Icon className="h-3.5 w-3.5" strokeWidth={1.75} />
              {label}
            </span>
          ))}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-7 overflow-y-auto py-7">
        {empty && (
          <div className="animate-rise pt-6">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-flare-50 text-flare-600">
              <Sparkles className="h-6 w-6" strokeWidth={1.75} />
            </span>
            <h2 className="display mt-5 text-[1.6rem] font-medium leading-snug text-ink">
              What do you want to figure out?
            </h2>
            <p className="mt-2 max-w-md text-[0.9rem] text-ink-muted">
              I read your knowledge base, the GTM strategy you generated, your content
              library, and saved memory — then answer with citations.
            </p>
            <div className="mt-6 grid gap-2.5 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="card card-flat lift px-4 py-3 text-left text-[0.875rem] text-ink-muted hover:text-ink"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) =>
          m.role === "user" ? (
            <UserMessage key={i} content={m.content} />
          ) : (
            <AssistantMessage key={i} message={m} />
          )
        )}

        {error && (
          <div className="alert alert-danger">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Couldn&apos;t complete that</p>
              <p className="opacity-80">{error}</p>
            </div>
          </div>
        )}
      </div>

      <form onSubmit={submit} className="shrink-0 border-t border-hairline bg-canvas/80 py-4 backdrop-blur">
        <div className="flex items-end gap-2 rounded-2xl border border-hairline-strong bg-surface p-2 shadow-sm focus-within:border-flare-600">
          <textarea
            ref={taRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
            }}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Ask your strategist…"
            className="max-h-40 flex-1 resize-none bg-transparent px-2.5 py-2 text-[0.95rem] text-ink outline-none placeholder:text-ink-faint"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-flare-600 text-white transition-colors hover:bg-flare-700 disabled:opacity-40"
            aria-label="Send"
          >
            <ArrowUp className="h-4.5 w-4.5" strokeWidth={2.25} />
          </button>
        </div>
        <p className="mt-2 px-1 text-center text-[0.7rem] text-ink-faint">
          Grounded answers only — it won&apos;t invent facts outside your company&apos;s data.
        </p>
      </form>
    </div>
  );
}
