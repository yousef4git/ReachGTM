import { useEffect, useRef, useState, useCallback } from "react";
import type { AgentEvent } from "@/types";
import { AgentEventType } from "@/types";

interface UseAgentStreamResult {
  events: AgentEvent[];
  isStreaming: boolean;
  error: string | null;
  start: (sessionId: string) => void;
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

  const start = useCallback((sessionId: string) => {
    stop();
    setEvents([]);
    setError(null);
    setIsStreaming(true);

    const token = localStorage.getItem("access_token") ?? "";
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/strategy/generate/stream?session_id=${sessionId}&token=${token}`;
    const es = new EventSource(url);
    esRef.current = es;

    const handleEvent = (type: AgentEventType) => (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev, { ...data, event: type }]);
        if (type === AgentEventType.DONE || type === AgentEventType.AGENT_COMPLETE) {
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
