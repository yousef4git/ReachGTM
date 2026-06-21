"use client";

import { useEffect, useState } from "react";
import { Check, Copy, Users } from "lucide-react";
import { teamApi } from "@/lib/api";
import { getRole } from "@/lib/auth";
import type { TeamRole } from "@/types";

// Roles an owner/admin is allowed to invite as.
const INVITABLE_ROLES: TeamRole[] = ["member", "admin"];

export default function TeamPage() {
  // null = not yet resolved (avoids hydration mismatch since role comes from localStorage)
  const [role, setRole] = useState<string | null>(null);
  const [resolved, setResolved] = useState(false);

  const [inviteRole, setInviteRole] = useState<TeamRole>("member");
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setRole(getRole());
    setResolved(true);
  }, []);

  const canInvite = role === "owner" || role === "admin";

  // Build the absolute invite URL the teammate will open. The backend returns a
  // relative path (/register?invite=...); prefix it with the current origin.
  function toAbsoluteUrl(path: string): string {
    if (typeof window === "undefined") return path;
    return `${window.location.origin}${path}`;
  }

  async function handleGenerate() {
    setError(null);
    setCopied(false);
    setInviteUrl(null);
    setLoading(true);
    try {
      const res = await teamApi.createInvite({ role: inviteRole });
      setInviteUrl(toAbsoluteUrl(res.invite_url));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create invite");
    } finally {
      setLoading(false);
    }
  }

  async function handleCopy() {
    if (!inviteUrl) return;
    try {
      await navigator.clipboard.writeText(inviteUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard may be unavailable (e.g. insecure context); ignore silently.
    }
  }

  if (!resolved) {
    return (
      <main className="p-8">
        <p className="text-sm text-gray-500">Loading...</p>
      </main>
    );
  }

  if (!canInvite) {
    return (
      <main className="mx-auto max-w-3xl p-8">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
          <Users className="h-6 w-6" /> Team
        </h1>
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-6">
          <p className="text-sm font-medium text-amber-800">You don&apos;t have access</p>
          <p className="mt-1 text-sm text-amber-700">
            Only workspace owners and admins can invite teammates. Ask an admin if you need access.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="flex items-center gap-2 text-2xl font-bold text-gray-900">
        <Users className="h-6 w-6" /> Team
      </h1>
      <p className="mt-1 text-sm text-gray-500">Invite teammates to your ReachGTM workspace.</p>

      {/* Invite a teammate */}
      <section className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Invite a teammate</h2>
        <p className="mt-1 text-sm text-gray-500">
          Choose a role and generate a one-time invite link to share.
        </p>

        <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="sm:w-48">
            <label className="block text-sm font-medium text-gray-700">Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as TeamRole)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm capitalize focus:border-blue-500 focus:outline-none"
            >
              {INVITABLE_ROLES.map((r) => (
                <option key={r} value={r} className="capitalize">
                  {r}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate invite link"}
          </button>
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        {inviteUrl && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Invite link</label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={inviteUrl}
                onFocus={(e) => e.currentTarget.select()}
                className="w-full rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-700 focus:outline-none"
              />
              <button
                type="button"
                onClick={handleCopy}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              Share this link with your teammate. They&apos;ll set their email and password to join.
            </p>
          </div>
        )}
      </section>

      {/* Member list and settings are added by issues #30 / #31. */}
    </main>
  );
}
