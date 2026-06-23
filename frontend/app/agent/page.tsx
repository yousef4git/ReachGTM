import { MessageSquare } from "lucide-react";

export default function AgentPage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col items-center px-5 py-28 text-center sm:px-8">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-ink text-canvas">
        <MessageSquare className="h-6 w-6" strokeWidth={1.75} />
      </span>
      <p className="eyebrow mt-7">Epic 2</p>
      <h1 className="display mt-3 text-[2.75rem] font-medium leading-tight text-ink">
        AI chat is on the way
      </h1>
      <p className="mt-3 max-w-md text-[1rem] leading-relaxed text-ink-muted">
        A conversational interface to interrogate your strategies and refine
        content with the agents. Landing in the next epic.
      </p>
    </main>
  );
}
