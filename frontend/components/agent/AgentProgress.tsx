import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";
import { Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

const AGENT_ORDER = ["research", "strategy", "content", "brand_alignment"];
const AGENT_LABELS: Record<string, string> = {
  research: "Research",
  strategy: "Strategy",
  content: "Content",
  brand_alignment: "Brand alignment",
};

type AgentStatus = "pending" | "running" | "complete" | "error";

function getAgentStatus(agent: string, events: AgentEvent[]): AgentStatus {
  const agentEvents = events.filter((e) => e.agent === agent);
  if (agentEvents.some((e) => e.event === AgentEventType.ERROR)) return "error";
  if (agentEvents.some((e) => e.event === AgentEventType.AGENT_COMPLETE)) return "complete";
  if (agentEvents.some((e) => e.event === AgentEventType.AGENT_START)) return "running";
  return "pending";
}

function Node({ status, index }: { status: AgentStatus; index: number }) {
  if (status === "complete") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-success text-canvas">
        <Check className="h-4 w-4" strokeWidth={2.5} />
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-danger text-canvas">
        <X className="h-4 w-4" strokeWidth={2.5} />
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="signal-pulse flex h-8 w-8 items-center justify-center rounded-full bg-flare-600 mono text-[0.75rem] font-semibold text-white">
        0{index + 1}
      </span>
    );
  }
  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full border border-hairline-strong bg-surface mono text-[0.75rem] font-medium text-ink-faint">
      0{index + 1}
    </span>
  );
}

export function AgentProgress({ events }: { events: AgentEvent[] }) {
  return (
    <div className="py-1">
      {AGENT_ORDER.map((agent, i) => {
        const status = getAgentStatus(agent, events);
        const latestMessage = events
          .filter((e) => e.agent === agent && e.message)
          .at(-1)?.message;
        const last = i === AGENT_ORDER.length - 1;
        return (
          <div key={agent} className="flex gap-4">
            <div className="flex flex-col items-center">
              <Node status={status} index={i} />
              {!last && (
                <div
                  className={cn(
                    "my-1 w-px flex-1",
                    status === "complete" ? "bg-success/40" : "bg-hairline"
                  )}
                />
              )}
            </div>
            <div className={cn("pb-7", last && "pb-0")}>
              <div className="flex items-center gap-2">
                <p
                  className={cn(
                    "text-[0.9375rem] font-semibold",
                    status === "pending" ? "text-ink-faint" : "text-ink"
                  )}
                >
                  {AGENT_LABELS[agent]}
                </p>
                {status === "running" && (
                  <span className="chip chip-flare !py-0.5 !text-[0.625rem]">
                    Working
                  </span>
                )}
              </div>
              {latestMessage && (
                <p className="mt-1 text-[0.8125rem] leading-relaxed text-ink-muted">
                  {latestMessage}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
