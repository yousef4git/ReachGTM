import { create } from "zustand";
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

export const useStore = create<AppStore>((set) => ({
  currentStrategy: null,
  contentAssets: [],
  knowledgeDocs: [],
  setStrategy: (s) => set({ currentStrategy: s }),
  addContentAsset: (a) => set((state) => ({ contentAssets: [...state.contentAssets, a] })),
  setContentAssets: (assets) => set({ contentAssets: assets }),
  removeContentAsset: (id) => set((state) => ({
    contentAssets: state.contentAssets.filter((a) => a.id !== id),
  })),
  setKnowledgeDocs: (docs) => set({ knowledgeDocs: docs }),
  addKnowledgeDoc: (doc) => set((state) => ({
    knowledgeDocs: [...state.knowledgeDocs, doc],
  })),
}));
