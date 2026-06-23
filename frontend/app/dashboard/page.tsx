"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Sparkles,
  FileText,
  BookOpen,
  Users,
  ArrowRight,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getRole } from "@/lib/auth";

const ACTIONS = [
  {
    href: "/strategy/new",
    title: "New GTM Strategy",
    description: "Run the research → strategy → content pipeline on a new goal.",
    icon: Sparkles,
    accent: "text-blue-600 bg-blue-50",
  },
  {
    href: "/content",
    title: "Content Library",
    description: "Browse and manage generated content assets.",
    icon: FileText,
    accent: "text-purple-600 bg-purple-50",
  },
  {
    href: "/knowledge",
    title: "Knowledge Base",
    description: "Upload brand docs that ground the agents' output.",
    icon: BookOpen,
    accent: "text-emerald-600 bg-emerald-50",
  },
  {
    href: "/team",
    title: "Team",
    description: "Invite members and manage roles and workspace settings.",
    icon: Users,
    accent: "text-amber-600 bg-amber-50",
  },
];

export default function DashboardPage() {
  const { logout } = useAuth();
  const [role, setRole] = useState<string | null>(null);

  // Read the role from the stored token on the client only.
  useEffect(() => setRole(getRole()), []);

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
          <p className="mt-1 text-gray-500">
            Your AI go-to-market workspace
            {role ? (
              <>
                {" "}
                · signed in as{" "}
                <span className="font-medium capitalize text-gray-700">{role}</span>
              </>
            ) : null}
          </p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:bg-gray-50"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {ACTIONS.map(({ href, title, description, icon: Icon, accent }) => (
          <Link
            key={href}
            href={href}
            className="group flex flex-col rounded-xl border bg-white p-5 transition-shadow hover:shadow-md"
          >
            <span className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${accent}`}>
              <Icon className="h-5 w-5" />
            </span>
            <h2 className="mt-4 font-semibold text-gray-900">{title}</h2>
            <p className="mt-1 flex-1 text-sm text-gray-500">{description}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-blue-600">
              Open
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>
        ))}
      </div>

      <Link
        href="/strategy/new"
        className="mt-8 flex items-center justify-between rounded-xl bg-gray-900 p-6 text-white transition-colors hover:bg-gray-800"
      >
        <div>
          <h2 className="text-lg font-semibold">Start a new strategy</h2>
          <p className="mt-1 text-sm text-gray-300">
            Give the agents a goal and watch the pipeline stream live.
          </p>
        </div>
        <Sparkles className="h-6 w-6" />
      </Link>
    </main>
  );
}
