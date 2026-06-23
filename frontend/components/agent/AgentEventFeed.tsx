import { useEffect, useRef } from "react";
import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

interface AgentEventFeedProps {
  events: AgentEvent[];
}

const eventDot: Record<string, string> = {
  [AgentEventType.AGENT_START]: "bg-blue-500",
  [AgentEventType.AGENT_PROGRESS]: "bg-gray-300",
  [AgentEventType.AGENT_OUTPUT]: "bg-emerald-500",
  [AgentEventType.AGENT_COMPLETE]: "bg-emerald-600",
  [AgentEventType.ERROR]: "bg-red-500",
  [AgentEventType.DONE]: "bg-violet-500",
};

const eventLabels: Record<string, string> = {
  [AgentEventType.AGENT_START]: "started",
  [AgentEventType.AGENT_PROGRESS]: "",
  [AgentEventType.AGENT_OUTPUT]: "output",
  [AgentEventType.AGENT_COMPLETE]: "complete",
  [AgentEventType.ERROR]: "error",
  [AgentEventType.DONE]: "done",
};

export function AgentEventFeed({ events }: AgentEventFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-hairline p-6 text-center text-sm text-ink-muted">
        Events will appear here as agents run.
      </div>
    );
  }

  return (
    <div className="max-h-80 overflow-y-auto rounded-xl border border-hairline bg-canvas p-3">
      <ul className="space-y-1">
        {events.map((evt, i) => (
          <li
            key={i}
            className="animate-rise flex items-start gap-2.5 rounded-lg px-2 py-1.5 text-xs"
          >
            <span
              className={`mt-1 h-2 w-2 shrink-0 rounded-full ${eventDot[evt.event] ?? "bg-gray-300"}`}
              aria-hidden
            />
            <div className="min-w-0">
              <span className="font-semibold text-ink">{evt.agent ?? "system"}</span>
              {eventLabels[evt.event] && (
                <span className="ml-1.5 text-ink-muted">{eventLabels[evt.event]}</span>
              )}
              {evt.message && (
                <p className="mt-0.5 break-words text-ink-muted">{evt.message}</p>
              )}
            </div>
          </li>
        ))}
        <div ref={bottomRef} />
      </ul>
    </div>
  );
}
