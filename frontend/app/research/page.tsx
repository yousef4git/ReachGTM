import { Search } from "lucide-react";

export default function ResearchPage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col items-center px-5 py-28 text-center sm:px-8">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-ink text-canvas">
        <Search className="h-6 w-6" strokeWidth={1.75} />
      </span>
      <p className="eyebrow mt-7">Epic 2</p>
      <h1 className="display mt-3 text-[2.75rem] font-medium leading-tight text-ink">
        Standalone research
      </h1>
      <p className="mt-3 max-w-md text-[1rem] leading-relaxed text-ink-muted">
        Run the research agent on its own — market scans, competitor maps, and
        ICP intelligence you can reuse across strategies. Coming soon.
      </p>
    </main>
  );
}
