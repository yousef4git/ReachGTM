import { useEffect, useRef } from "react";
import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

interface AgentEventFeedProps {
  events: AgentEvent[];
}

const eventDot: Record<string, string> = {
  [AgentEventType.AGENT_START]: "bg-flare-500",
  [AgentEventType.AGENT_PROGRESS]: "bg-ink-faint",
  [AgentEventType.AGENT_OUTPUT]: "bg-success",
  [AgentEventType.AGENT_COMPLETE]: "bg-success",
  [AgentEventType.ERROR]: "bg-danger",
  [AgentEventType.DONE]: "bg-ink",
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
      <div className="rounded-lg border border-dashed border-hairline-strong p-6 text-center text-[0.8125rem] text-ink-muted">
        Events will appear here as agents run.
      </div>
    );
  }

  return (
    <div className="max-h-80 overflow-y-auto rounded-lg border border-hairline bg-sunken p-3">
      <ul className="space-y-0.5">
        {events.map((evt, i) => (
          <li
            key={i}
            className="animate-fade flex items-start gap-2.5 rounded-md px-2 py-1.5 text-[0.75rem] hover:bg-surface"
          >
            <span
              className={`mt-1 h-1.5 w-1.5 shrink-0 rounded-full ${eventDot[evt.event] ?? "bg-ink-faint"}`}
              aria-hidden
            />
            <div className="min-w-0 flex-1">
              <span className="mono text-[0.6875rem] font-semibold uppercase tracking-wider text-ink">
                {evt.agent ?? "system"}
              </span>
              {eventLabels[evt.event] && (
                <span className="mono ml-1.5 text-[0.6875rem] uppercase tracking-wider text-flare-700">
                  {eventLabels[evt.event]}
                </span>
              )}
              {evt.message && (
                <p className="mt-0.5 break-words text-[0.8125rem] text-ink-muted">
                  {evt.message}
                </p>
              )}
            </div>
          </li>
        ))}
        <div ref={bottomRef} />
      </ul>
    </div>
  );
}
