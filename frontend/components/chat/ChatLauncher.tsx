"use client";

import { useRef, useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, ArrowUp, X, Maximize2, RotateCcw, MessageSquare } from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { AssistantMessage, UserMessage, SUGGESTIONS } from "@/components/chat/chatParts";
import { cn } from "@/lib/utils";

const HIDDEN_PREFIXES = ["/login", "/register", "/agent"];

/**
 * App-wide floating chatbot. Mounted in AppChrome so it's reachable from every
 * page; the conversation lives in a session-scoped store, so opening it on any
 * page continues the same thread (and survives navigation + refresh).
 */
export function ChatLauncher() {
  const pathname = usePathname();
  const { messages, isStreaming, error, isOpen, toggle, close, send, reset } = useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (isOpen) scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isOpen]);

  const hidden = HIDDEN_PREFIXES.some((p) => pathname === p || pathname?.startsWith(`${p}/`));
  if (hidden) return null;

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
    <>
      {/* Launcher button */}
      <button
        onClick={toggle}
        aria-label={isOpen ? "Close assistant" : "Open assistant"}
        className={cn(
          "fixed bottom-5 right-5 z-50 flex h-13 w-13 items-center justify-center rounded-full shadow-lg transition-all duration-300",
          "h-13 w-13 hover:scale-105",
          isOpen ? "bg-ink text-canvas" : "bg-flare-600 text-white hover:bg-flare-700"
        )}
        style={{ height: "3.25rem", width: "3.25rem" }}
      >
        {isOpen ? <X className="h-5 w-5" /> : <MessageSquare className="h-5 w-5" strokeWidth={2} />}
        {!isOpen && messages.length > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-flare-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-canvas ring-2 ring-flare-600" />
          </span>
        )}
      </button>

      {/* Panel */}
      <div
        className={cn(
          "fixed bottom-20 right-5 z-50 flex w-[min(26rem,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-hairline-strong bg-canvas shadow-xl transition-all duration-300",
          isOpen
            ? "pointer-events-auto translate-y-0 opacity-100"
            : "pointer-events-none translate-y-4 opacity-0"
        )}
        style={{ height: "min(34rem, calc(100vh - 7rem))" }}
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center justify-between border-b border-hairline bg-surface px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink text-canvas">
              <Sparkles className="h-4 w-4" strokeWidth={2} />
            </span>
            <div>
              <p className="text-[0.875rem] font-semibold leading-tight text-ink">Strategy Desk</p>
              <p className="text-[0.6875rem] leading-tight text-ink-faint">Grounded in your company</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <button
                onClick={reset}
                className="rounded-lg p-1.5 text-ink-faint hover:bg-sunken hover:text-ink"
                title="New conversation"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            )}
            <Link
              href="/agent"
              onClick={close}
              className="rounded-lg p-1.5 text-ink-faint hover:bg-sunken hover:text-ink"
              title="Open full page"
            >
              <Maximize2 className="h-4 w-4" />
            </Link>
            <button
              onClick={close}
              className="rounded-lg p-1.5 text-ink-faint hover:bg-sunken hover:text-ink"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Thread */}
        <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
          {empty ? (
            <div className="animate-rise">
              <p className="text-[0.9rem] font-medium text-ink">Ask your strategist</p>
              <p className="mt-1 text-[0.8125rem] leading-relaxed text-ink-muted">
                Answers cite your knowledge base, strategy, content, and memory.
              </p>
              <div className="mt-4 flex flex-col gap-2">
                {SUGGESTIONS.slice(0, 3).map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="card card-flat px-3 py-2 text-left text-[0.8125rem] text-ink-muted transition-colors hover:text-ink"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) =>
              m.role === "user" ? (
                <UserMessage key={i} content={m.content} />
              ) : (
                <AssistantMessage key={i} message={m} />
              )
            )
          )}
          {error && <p className="text-[0.8125rem] text-danger">{error}</p>}
        </div>

        {/* Composer */}
        <form onSubmit={submit} className="shrink-0 border-t border-hairline bg-surface p-3">
          <div className="flex items-end gap-2 rounded-xl border border-hairline-strong bg-canvas p-1.5 focus-within:border-flare-600">
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
              }}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Ask anything…"
              className="max-h-28 flex-1 resize-none bg-transparent px-2 py-1.5 text-[0.875rem] text-ink outline-none placeholder:text-ink-faint"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-flare-600 text-white transition-colors hover:bg-flare-700 disabled:opacity-40"
              aria-label="Send"
            >
              <ArrowUp className="h-4 w-4" strokeWidth={2.25} />
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
