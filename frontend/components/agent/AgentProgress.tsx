import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

const AGENT_ORDER = ["research", "strategy", "content", "brand_alignment"];
const AGENT_LABELS: Record<string, string> = {
  research: "Research",
  strategy: "Strategy",
  content: "Content",
  brand_alignment: "Brand Alignment",
};

type AgentStatus = "pending" | "running" | "complete" | "error";

function getAgentStatus(agent: string, events: AgentEvent[]): AgentStatus {
  const agentEvents = events.filter((e) => e.agent === agent);
  if (agentEvents.some((e) => e.event === AgentEventType.ERROR)) return "error";
  if (agentEvents.some((e) => e.event === AgentEventType.AGENT_COMPLETE)) return "complete";
  if (agentEvents.some((e) => e.event === AgentEventType.AGENT_START)) return "running";
  return "pending";
}

const StatusDot = ({ status }: { status: AgentStatus }) => {
  const classes: Record<AgentStatus, string> = {
    pending: "bg-gray-300",
    running: "bg-blue-500 animate-pulse",
    complete: "bg-green-500",
    error: "bg-red-500",
  };
  return <span className={`inline-block h-3 w-3 rounded-full ${classes[status]}`} />;
};

export function AgentProgress({ events }: { events: AgentEvent[] }) {
  return (
    <div className="space-y-4 py-4">
      {AGENT_ORDER.map((agent, i) => {
        const status = getAgentStatus(agent, events);
        const latestMessage = events
          .filter((e) => e.agent === agent && e.message)
          .at(-1)?.message;
        return (
          <div key={agent} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <StatusDot status={status} />
              {i < AGENT_ORDER.length - 1 && (
                <div className="mt-1 h-8 w-px bg-gray-200" />
              )}
            </div>
            <div className="pb-4">
              <p className={`text-sm font-medium ${status === "pending" ? "text-gray-400" : "text-gray-900"}`}>
                {AGENT_LABELS[agent]}
              </p>
              {latestMessage && (
                <p className="mt-0.5 text-xs text-gray-500">{latestMessage}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
