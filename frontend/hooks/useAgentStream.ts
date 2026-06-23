import { useEffect, useRef, useState, useCallback } from "react";
import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

interface UseAgentStreamResult {
  events: AgentEvent[];
  isStreaming: boolean;
  error: string | null;
  start: (sessionId: string, goal: string) => void;
  stop: () => void;
}

export function useAgentStream(): UseAgentStreamResult {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const stop = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setIsStreaming(false);
  }, []);

  const start = useCallback((sessionId: string, goal: string) => {
    stop();
    setEvents([]);
    setError(null);
    setIsStreaming(true);

    const token = localStorage.getItem("access_token") ?? "";
    // EventSource is GET-only and header-less, so token + goal travel as query
    // params; the backend GET /strategy/generate/stream self-authenticates.
    const params = new URLSearchParams({ session_id: sessionId, goal, token });
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/strategy/generate/stream?${params.toString()}`;
    const es = new EventSource(url);
    esRef.current = es;

    const handleEvent = (type: AgentEventType) => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev, { ...data, event: type }]);
        // Close only on the terminal `done` frame. The backend now emits
        // `persisted` (carrying the saved strategy_id) AFTER agent_complete,
        // so closing on agent_complete would race away the persistence event.
        if (type === AgentEventType.DONE) {
          stop();
        }
      } catch {
        setError("Failed to parse event");
      }
    };

    es.addEventListener(AgentEventType.AGENT_START, handleEvent(AgentEventType.AGENT_START));
    es.addEventListener(AgentEventType.AGENT_PROGRESS, handleEvent(AgentEventType.AGENT_PROGRESS));
    es.addEventListener(AgentEventType.AGENT_OUTPUT, handleEvent(AgentEventType.AGENT_OUTPUT));
    es.addEventListener(AgentEventType.AGENT_COMPLETE, handleEvent(AgentEventType.AGENT_COMPLETE));
    es.addEventListener(AgentEventType.PERSISTED, handleEvent(AgentEventType.PERSISTED));
    es.addEventListener(AgentEventType.DONE, handleEvent(AgentEventType.DONE));
    es.addEventListener(AgentEventType.ERROR, (e: MessageEvent) => {
      setError(e.data);
      stop();
    });

    es.onerror = () => {
      setError("SSE connection failed");
      stop();
    };
  }, [stop]);

  useEffect(() => () => stop(), [stop]);

  return { events, isStreaming, error, start, stop };
}
