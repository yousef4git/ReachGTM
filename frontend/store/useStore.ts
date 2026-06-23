import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { GTMStrategy, ContentAsset, KnowledgeDocument } from "@/types";

interface AppStore {
  currentStrategy: GTMStrategy | null;
  contentAssets: ContentAsset[];
  knowledgeDocs: KnowledgeDocument[];
  setStrategy: (s: GTMStrategy) => void;
  addContentAsset: (a: ContentAsset) => void;
  setContentAssets: (assets: ContentAsset[]) => void;
  removeContentAsset: (id: string) => void;
  setKnowledgeDocs: (docs: KnowledgeDocument[]) => void;
  addKnowledgeDoc: (doc: KnowledgeDocument) => void;
}

// Persisted to localStorage so freshly generated strategies and content survive
// a page refresh and are findable across the app (the backend list endpoints are
// still stubs — this is the durable client-side source until they land).
export const useStore = create<AppStore>()(
  persist(
    (set) => ({
      currentStrategy: null,
      contentAssets: [],
      knowledgeDocs: [],
      setStrategy: (s) => set({ currentStrategy: s }),
      addContentAsset: (a) => set((state) => ({ contentAssets: [...state.contentAssets, a] })),
      setContentAssets: (assets) => set({ contentAssets: assets }),
      removeContentAsset: (id) =>
        set((state) => ({
          contentAssets: state.contentAssets.filter((a) => a.id !== id),
        })),
      setKnowledgeDocs: (docs) => set({ knowledgeDocs: docs }),
      addKnowledgeDoc: (doc) =>
        set((state) => ({
          knowledgeDocs: [...state.knowledgeDocs, doc],
        })),
    }),
    {
      name: "reachgtm-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentStrategy: state.currentStrategy,
        contentAssets: state.contentAssets,
        knowledgeDocs: state.knowledgeDocs,
      }),
    }
  )
);
