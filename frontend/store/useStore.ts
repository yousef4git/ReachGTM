import { create } from "zustand";
import type { GTMStrategy, ContentAsset } from "@/types";

interface AppStore {
  currentStrategy: GTMStrategy | null;
  contentAssets: ContentAsset[];
  setStrategy: (s: GTMStrategy) => void;
  addContentAsset: (a: ContentAsset) => void;
}

export const useStore = create<AppStore>((set) => ({
  currentStrategy: null,
  contentAssets: [],
  setStrategy: (s) => set({ currentStrategy: s }),
  addContentAsset: (a) => set((state) => ({ contentAssets: [...state.contentAssets, a] })),
}));
