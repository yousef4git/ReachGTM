import { useEffect, useRef } from "react";
import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

interface AgentEventFeedProps {
  events: AgentEvent[];
}

const eventColors: Record<string, string> = {
  [AgentEventType.AGENT_START]: "text-blue-600 border-l-blue-400",
  [AgentEventType.AGENT_PROGRESS]: "text-gray-600 border-l-gray-300",
  [AgentEventType.AGENT_OUTPUT]: "text-green-700 border-l-green-400",
  [AgentEventType.AGENT_COMPLETE]: "text-green-600 border-l-green-500",
  [AgentEventType.ERROR]: "text-red-600 border-l-red-500",
  [AgentEventType.DONE]: "text-purple-600 border-l-purple-500",
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
      <div className="rounded-lg border border-dashed border-gray-200 p-6 text-center text-sm text-gray-400">
        Events will appear here as agents run…
      </div>
    );
  }

  return (
    <div className="max-h-80 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-3">
      <div className="space-y-1.5">
        {events.map((evt, i) => (
          <div
            key={i}
            className={`border-l-2 pl-3 text-xs ${eventColors[evt.event] ?? "text-gray-500"}`}
          >
            <span className="font-medium">{evt.agent ?? "system"}</span>{" "}
            {eventLabels[evt.event] && (
              <span className="opacity-70">— {eventLabels[evt.event]}</span>
            )}
            {evt.message && <p className="mt-0.5 opacity-80">{evt.message}</p>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
