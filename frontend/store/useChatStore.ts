import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface ChatSource {
  filename: string;
  doc_type: string;
  similarity: number;
}

export interface ChatGrounding {
  kb_chunks: number;
  has_strategy: boolean;
  content_assets: number;
  memory_keys: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  grounding?: ChatGrounding;
  streaming?: boolean;
}

interface ChatStore {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  send: (text: string) => Promise<void>;
  reset: () => void;
}

// AbortController is not serializable, so it lives outside the store state.
let activeController: AbortController | null = null;

/**
 * Shared, session-scoped chatbot state.
 *
 * Persisted to sessionStorage so the conversation survives client-side
 * navigation AND a hard refresh, but is cleared when the browser session
 * (tab) closes — exactly "remember until the session is closed". Because the
 * store lives outside React, the floating launcher and the /agent page share
 * one continuous conversation.
 */
export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      messages: [],
      isStreaming: false,
      error: null,
      isOpen: false,

      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      toggle: () => set((s) => ({ isOpen: !s.isOpen })),

      reset: () => {
        activeController?.abort();
        activeController = null;
        set({ messages: [], error: null, isStreaming: false });
      },

      send: async (text: string) => {
        const question = text.trim();
        if (!question || get().isStreaming) return;

        const history = get().messages.map((m) => ({ role: m.role, content: m.content }));

        set((s) => ({
          error: null,
          isStreaming: true,
          messages: [
            ...s.messages,
            { role: "user", content: question } as ChatMessage,
            { role: "assistant", content: "", streaming: true } as ChatMessage,
          ],
        }));

        const patchAssistant = (patch: Partial<ChatMessage>) =>
          set((s) => {
            const next = [...s.messages];
            for (let i = next.length - 1; i >= 0; i--) {
              if (next[i].role === "assistant") {
                next[i] = { ...next[i], ...patch };
                break;
              }
            }
            return { messages: next };
          });

        const controller = new AbortController();
        activeController = controller;

        try {
          const token =
            typeof window !== "undefined" ? localStorage.getItem("access_token") ?? "" : "";
          const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
          const res = await fetch(`${base}/api/v1/chat/`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ message: question, history }),
            signal: controller.signal,
          });

          if (!res.ok || !res.body) throw new Error(`Chat request failed (${res.status})`);

          const reader = res.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let acc = "";

          const handleFrame = (frame: string) => {
            let event = "message";
            let data = "";
            for (const line of frame.split("\n")) {
              if (line.startsWith("event:")) event = line.slice(6).trim();
              else if (line.startsWith("data:")) data += line.slice(5).trim();
            }
            if (!data) return;
            let payload: Record<string, unknown>;
            try {
              payload = JSON.parse(data);
            } catch {
              return;
            }
            if (event === "token" && typeof payload.text === "string") {
              acc += payload.text;
              patchAssistant({ content: acc });
            } else if (event === "sources") {
              patchAssistant({
                sources: payload.sources as ChatSource[],
                grounding: payload.grounded as ChatGrounding,
              });
            } else if (event === "error") {
              set({ error: String(payload.message ?? "Chat failed") });
            }
          };

          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            let idx;
            while ((idx = buffer.indexOf("\n\n")) !== -1) {
              const frame = buffer.slice(0, idx);
              buffer = buffer.slice(idx + 2);
              if (frame.trim()) handleFrame(frame);
            }
          }
          if (buffer.trim()) handleFrame(buffer);
          patchAssistant({ streaming: false });
        } catch (err) {
          if ((err as Error).name !== "AbortError") {
            set({ error: (err as Error).message });
            patchAssistant({ streaming: false });
          }
        } finally {
          set({ isStreaming: false });
          activeController = null;
        }
      },
    }),
    {
      name: "reachgtm-chat",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? sessionStorage : (undefined as unknown as Storage)
      ),
      // Persist only the conversation + panel state, never transient streaming flags.
      partialize: (s) => ({ messages: s.messages, isOpen: s.isOpen }),
    }
  )
);
