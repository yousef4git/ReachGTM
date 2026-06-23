"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Sparkles, FileText, BookOpen, Users, ArrowRight } from "lucide-react";
import { getRole } from "@/lib/auth";

const ACTIONS = [
  {
    href: "/strategy/new",
    title: "New GTM Strategy",
    description: "Run the research, strategy, and content pipeline on a fresh goal.",
    icon: Sparkles,
    accent: "text-blue-600 bg-blue-50",
  },
  {
    href: "/content",
    title: "Content Library",
    description: "Browse and manage every generated content asset.",
    icon: FileText,
    accent: "text-violet-600 bg-violet-50",
  },
  {
    href: "/knowledge",
    title: "Knowledge Base",
    description: "Upload brand docs that ground the agents in your voice.",
    icon: BookOpen,
    accent: "text-emerald-600 bg-emerald-50",
  },
  {
    href: "/team",
    title: "Team",
    description: "Invite members, manage roles, and tune workspace settings.",
    icon: Users,
    accent: "text-amber-600 bg-amber-50",
  },
];

export default function DashboardPage() {
  const [role, setRole] = useState<string | null>(null);
  useEffect(() => setRole(getRole()), []);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10 sm:py-14">
      <header className="animate-rise">
        <h1 className="text-[2rem] font-semibold tracking-tight text-ink">
          Welcome back
        </h1>
        <p className="mt-1.5 text-[0.9375rem] text-ink-muted">
          Your AI go-to-market workspace
          {role ? (
            <>
              {" "}
              <span aria-hidden className="text-hairline">·</span>{" "}
              signed in as{" "}
              <span className="font-medium capitalize text-ink">{role}</span>
            </>
          ) : null}
        </p>
      </header>

      <div className="stagger mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {ACTIONS.map(({ href, title, description, icon: Icon, accent }) => (
          <Link
            key={href}
            href={href}
            className="card press group flex flex-col p-5 transition-shadow duration-200 hover:shadow-md"
          >
            <span
              className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${accent}`}
            >
              <Icon className="h-5 w-5" />
            </span>
            <h2 className="mt-4 text-[0.9375rem] font-semibold text-ink">{title}</h2>
            <p className="mt-1 flex-1 text-[0.8125rem] leading-relaxed text-ink-muted">
              {description}
            </p>
            <span className="mt-4 inline-flex items-center gap-1 text-[0.8125rem] font-medium text-blue-600">
              Open
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </span>
          </Link>
        ))}
      </div>

      <Link
        href="/strategy/new"
        className="animate-rise press mt-5 flex items-center justify-between rounded-2xl bg-ink p-6 text-white transition-colors duration-200 hover:opacity-95"
      >
        <div>
          <h2 className="text-[1.0625rem] font-semibold">Start a new strategy</h2>
          <p className="mt-1 text-[0.875rem] text-white/70">
            Give the agents a goal and watch the pipeline stream live.
          </p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/10">
          <Sparkles className="h-5 w-5" />
        </span>
      </Link>
    </main>
  );
}
