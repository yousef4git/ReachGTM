"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Compass,
  FileText,
  BookOpen,
  Users,
  ArrowUpRight,
  Search,
  Layers,
  ShieldCheck,
} from "lucide-react";
import { getRole } from "@/lib/auth";
import { useContentList } from "@/hooks/useContent";
import { knowledgeApi } from "@/lib/api";
import { useStore } from "@/store/useStore";
import type { KnowledgeDocument } from "@/types";

const PIPELINE = [
  { key: "research", label: "Research", icon: Search, blurb: "Web + knowledge grounding" },
  { key: "strategy", label: "Strategy", icon: Compass, blurb: "ICP, positioning, motion" },
  { key: "content", label: "Content", icon: FileText, blurb: "Emails, posts, ads, outlines" },
  { key: "brand", label: "Brand check", icon: ShieldCheck, blurb: "Voice + alignment scoring" },
];

const ACTIONS = [
  {
    href: "/content",
    title: "Content Library",
    description: "Browse and manage every generated asset.",
    icon: FileText,
  },
  {
    href: "/knowledge",
    title: "Knowledge Base",
    description: "Upload brand docs that ground the agents.",
    icon: BookOpen,
  },
  {
    href: "/team",
    title: "Team & workspace",
    description: "Invite teammates, manage roles and plan.",
    icon: Users,
  },
];

export default function DashboardPage() {
  const [role, setRole] = useState<string | null>(null);
  useEffect(() => setRole(getRole()), []);

  const { data: serverContent } = useContentList();
  const localContent = useStore((s) => s.contentAssets);
  const contentCount = (serverContent ?? localContent)?.length ?? 0;

  const localDocs = useStore((s) => s.knowledgeDocs);
  const { data: serverDocs } = useQuery<KnowledgeDocument[]>({
    queryKey: ["knowledge"],
    queryFn: () => knowledgeApi.list(),
  });
  const docCount = (serverDocs ?? localDocs)?.length ?? 0;

  const stats = [
    { label: "Content assets", value: contentCount, href: "/content" },
    { label: "Knowledge docs", value: docCount, href: "/knowledge" },
    { label: "Pipeline agents", value: 4, href: "/strategy/new" },
  ];

  return (
    <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8 sm:py-16">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <header className="animate-rise">
        <p className="eyebrow">GTM Command Desk</p>
        <h1 className="display mt-3 text-[2.75rem] font-medium leading-[1.02] text-ink sm:text-[3.5rem]">
          Welcome back.
        </h1>
        <p className="mt-3 max-w-xl text-[1.0625rem] leading-relaxed text-ink-muted">
          Hand the agents a goal and watch a complete go-to-market plan come
          together — research, strategy, and content, end to end.
          {role ? (
            <>
              {" "}
              Signed in as{" "}
              <span className="font-semibold capitalize text-ink">{role}</span>.
            </>
          ) : null}
        </p>
      </header>

      {/* ── Launch panel (the story) ─────────────────────────────────────── */}
      <section className="animate-rise mt-10 overflow-hidden rounded-2xl bg-ink text-canvas shadow-lg">
        <div className="flex flex-col gap-8 p-7 sm:p-9 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-md">
            <p className="eyebrow !text-flare-400">The pipeline</p>
            <h2 className="display mt-2.5 text-[1.875rem] font-medium leading-tight">
              Launch a new strategy
            </h2>
            <p className="mt-3 text-[0.9375rem] leading-relaxed text-canvas/65">
              Four specialist agents run in sequence and stream their thinking
              live. Most plans land in under two minutes.
            </p>
            <Link
              href="/strategy/new"
              className="btn btn-flare mt-6 px-5 py-3 text-[0.9375rem]"
            >
              <Compass className="h-4 w-4" />
              Start a strategy
            </Link>
          </div>

          {/* Pipeline rail */}
          <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:max-w-md">
            {PIPELINE.map((step, i) => (
              <li
                key={step.key}
                className="relative rounded-xl border border-white/10 bg-white/[0.04] p-3.5"
              >
                <span className="mono text-[0.6875rem] text-flare-400">
                  0{i + 1}
                </span>
                <step.icon className="mt-2 h-5 w-5 text-canvas/90" strokeWidth={1.75} />
                <p className="mt-2 text-[0.8125rem] font-semibold leading-tight">
                  {step.label}
                </p>
                <p className="mt-1 text-[0.6875rem] leading-snug text-canvas/45">
                  {step.blurb}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ── Stats ────────────────────────────────────────────────────────── */}
      <section className="stagger mt-5 grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Link
            key={s.label}
            href={s.href}
            className="card lift group flex items-end justify-between p-5"
          >
            <div>
              <p className="eyebrow">{s.label}</p>
              <p className="display mt-2 text-[2.75rem] font-medium leading-none text-ink tabular-nums">
                {s.value}
              </p>
            </div>
            <ArrowUpRight className="h-5 w-5 text-ink-faint transition-colors group-hover:text-flare-600" />
          </Link>
        ))}
      </section>

      {/* ── Quick actions ────────────────────────────────────────────────── */}
      <section className="mt-12">
        <div className="flex items-center gap-3">
          <Layers className="h-4 w-4 text-ink-faint" />
          <h2 className="eyebrow !text-ink-muted">Jump back in</h2>
          <div className="rule flex-1" />
        </div>

        <div className="stagger mt-5 grid gap-4 sm:grid-cols-3">
          {ACTIONS.map(({ href, title, description, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="card lift group flex flex-col p-5"
            >
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-sunken text-ink transition-colors group-hover:bg-flare-50 group-hover:text-flare-700">
                <Icon className="h-5 w-5" strokeWidth={1.75} />
              </span>
              <h3 className="mt-4 text-[0.9375rem] font-semibold text-ink">
                {title}
              </h3>
              <p className="mt-1 flex-1 text-[0.8125rem] leading-relaxed text-ink-muted">
                {description}
              </p>
              <span className="mt-4 inline-flex items-center gap-1 text-[0.8125rem] font-semibold text-ink">
                Open
                <ArrowUpRight className="h-4 w-4 text-flare-600 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </span>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
