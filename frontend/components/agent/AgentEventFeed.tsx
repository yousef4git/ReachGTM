import type { AgentEvent } from "@/types";
export function AgentEventFeed({ events }: { events: AgentEvent[] }) {
  return <div className="text-xs text-gray-400">{events.length} events — Epic 2</div>;
}
