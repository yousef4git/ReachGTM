"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Users } from "lucide-react";
import { teamApi } from "@/lib/api";
import { getRole, getUserId } from "@/lib/auth";
import type {
  AssignableRole,
  TeamMember,
  TeamRole,
  TeamSettings,
  WorkspacePlan,
} from "@/types";

// Roles an owner/admin is allowed to invite as.
const INVITABLE_ROLES: TeamRole[] = ["member", "admin"];

// Selectable plans. Mirrors PLAN_SEAT_LIMITS in backend/app/api/team.py.
const PLANS: { value: WorkspacePlan; label: string }[] = [
  { value: "free", label: "Free" },
  { value: "pro", label: "Pro" },
  { value: "enterprise", label: "Enterprise" },
];

export default function TeamPage() {
  // null = not yet resolved (avoids hydration mismatch since role comes from localStorage)
  const [role, setRole] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [resolved, setResolved] = useState(false);

  const [inviteRole, setInviteRole] = useState<TeamRole>("member");
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Members table state.
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);
  const [pendingUserId, setPendingUserId] = useState<string | null>(null);

  // Workspace settings state (issue #31).
  const [settings, setSettings] = useState<TeamSettings | null>(null);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [nameDraft, setNameDraft] = useState("");

  const canInvite = role === "owner" || role === "admin";
  const isOwner = role === "owner";

  const loadMembers = useCallback(async () => {
    setMembersError(null);
    setMembersLoading(true);
    try {
      setMembers(await teamApi.listMembers());
    } catch (e: unknown) {
      setMembersError(e instanceof Error ? e.message : "Failed to load members");
    } finally {
      setMembersLoading(false);
    }
  }, []);

  const loadSettings = useCallback(async () => {
    setSettingsError(null);
    setSettingsLoading(true);
    try {
      const s = await teamApi.getSettings();
      setSettings(s);
      setNameDraft(s.name);
    } catch (e: unknown) {
      setSettingsError(e instanceof Error ? e.message : "Failed to load settings");
    } finally {
      setSettingsLoading(false);
    }
  }, []);

  useEffect(() => {
    setRole(getRole());
    setUserId(getUserId());
    setResolved(true);
  }, []);

  // Owners and admins can view the members list and workspace settings.
  useEffect(() => {
    if (resolved && canInvite) {
      void loadMembers();
      void loadSettings();
    }
  }, [resolved, canInvite, loadMembers, loadSettings]);

  async function handleRenameWorkspace() {
    if (!settings) return;
    const next = nameDraft.trim();
    if (!next || next === settings.name) return;
    setSettingsError(null);
    setSettingsSaving(true);
    try {
      const updated = await teamApi.updateSettings({ name: next });
      setSettings(updated);
      setNameDraft(updated.name);
    } catch (e: unknown) {
      setSettingsError(e instanceof Error ? e.message : "Failed to rename workspace");
    } finally {
      setSettingsSaving(false);
    }
  }

  async function handlePlanChange(plan: WorkspacePlan) {
    if (!settings || plan === settings.plan) return;
    setSettingsError(null);
    setSettingsSaving(true);
    try {
      const updated = await teamApi.updateSettings({ plan });
      setSettings(updated);
    } catch (e: unknown) {
      setSettingsError(e instanceof Error ? e.message : "Failed to change plan");
    } finally {
      setSettingsSaving(false);
    }
  }

  async function handleRoleChange(member: TeamMember, nextRole: AssignableRole) {
    setMembersError(null);
    setPendingUserId(member.id);
    try {
      await teamApi.updateMemberRole(member.id, nextRole);
      await loadMembers();
    } catch (e: unknown) {
      setMembersError(e instanceof Error ? e.message : "Failed to update role");
    } finally {
      setPendingUserId(null);
    }
  }

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

      {/* Members */}
      <section className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Members</h2>
            <p className="mt-1 text-sm text-gray-500">
              {isOwner
                ? "Promote or demote teammates between member and admin."
                : "Everyone in your workspace."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadMembers()}
            disabled={membersLoading}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {membersLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {membersError && <p className="mt-3 text-sm text-red-600">{membersError}</p>}

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide text-gray-500">
                <th className="py-2 pr-4 font-medium">Email</th>
                <th className="py-2 pr-4 font-medium">Role</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                {isOwner && <th className="py-2 font-medium text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {members.length === 0 && !membersLoading && (
                <tr>
                  <td colSpan={isOwner ? 4 : 3} className="py-4 text-sm text-gray-500">
                    No members yet.
                  </td>
                </tr>
              )}
              {members.map((m) => {
                const isSelf = m.id === userId;
                const isOwnerRow = m.role === "owner";
                // Owner can act on every row except the owner row and their own row.
                const showActions = isOwner && !isOwnerRow && !isSelf;
                const busy = pendingUserId === m.id;
                return (
                  <tr key={m.id} className="border-b last:border-0">
                    <td className="py-3 pr-4 text-gray-900">
                      {m.email}
                      {isSelf && <span className="ml-2 text-xs text-gray-400">(you)</span>}
                    </td>
                    <td className="py-3 pr-4">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize text-gray-700">
                        {m.role}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <span
                        className={
                          m.is_active
                            ? "inline-flex items-center gap-1 text-xs font-medium text-green-700"
                            : "inline-flex items-center gap-1 text-xs font-medium text-gray-400"
                        }
                      >
                        {m.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    {isOwner && (
                      <td className="py-3 text-right">
                        {showActions ? (
                          m.role === "member" ? (
                            <button
                              type="button"
                              onClick={() => void handleRoleChange(m, "admin")}
                              disabled={busy}
                              className="rounded-md border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-50"
                            >
                              {busy ? "Saving..." : "Promote to admin"}
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => void handleRoleChange(m, "member")}
                              disabled={busy}
                              className="rounded-md border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                            >
                              {busy ? "Saving..." : "Demote to member"}
                            </button>
                          )
                        ) : (
                          <span className="text-xs text-gray-300">·</span>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Workspace settings (issue #31) */}
      <section className="mt-6 rounded-xl border bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Workspace settings</h2>
            <p className="mt-1 text-sm text-gray-500">
              {isOwner
                ? "Manage your workspace name, plan, and seat usage."
                : "Your workspace plan and seat usage."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadSettings()}
            disabled={settingsLoading}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {settingsLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {settingsError && <p className="mt-3 text-sm text-red-600">{settingsError}</p>}

        {!settings && settingsLoading && (
          <p className="mt-4 text-sm text-gray-500">Loading settings...</p>
        )}

        {settings && (
          <div className="mt-4 space-y-6">
            {/* Workspace name */}
            <div>
              <label className="block text-sm font-medium text-gray-700">Workspace name</label>
              {isOwner ? (
                <div className="mt-1 flex items-center gap-2">
                  <input
                    type="text"
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    className="w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => void handleRenameWorkspace()}
                    disabled={
                      settingsSaving ||
                      !nameDraft.trim() ||
                      nameDraft.trim() === settings.name
                    }
                    className="shrink-0 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {settingsSaving ? "Saving..." : "Save"}
                  </button>
                </div>
              ) : (
                <p className="mt-1 text-sm text-gray-900">{settings.name}</p>
              )}
            </div>

            {/* Plan */}
            <div>
              <label className="block text-sm font-medium text-gray-700">Plan</label>
              {isOwner ? (
                <select
                  value={settings.plan}
                  onChange={(e) => void handlePlanChange(e.target.value as WorkspacePlan)}
                  disabled={settingsSaving}
                  className="mt-1 w-full max-w-sm rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
                >
                  {PLANS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="mt-1">
                  <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize text-gray-700">
                    {settings.plan}
                  </span>
                </p>
              )}
              {isOwner && (
                <p className="mt-2 text-xs text-amber-700">
                  Note: billing is not yet integrated. Switching plans takes effect
                  immediately and does not charge a payment method.
                </p>
              )}
            </div>

            {/* Seat usage */}
            <div>
              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">Seats</label>
                <span className="text-sm text-gray-600">
                  {settings.seat_count} / {settings.seat_limit}
                </span>
              </div>
              <div className="mt-2 h-2 w-full max-w-sm overflow-hidden rounded-full bg-gray-100">
                <div
                  className={
                    settings.seat_count >= settings.seat_limit
                      ? "h-full rounded-full bg-red-500"
                      : "h-full rounded-full bg-blue-600"
                  }
                  style={{
                    width: `${Math.min(
                      100,
                      settings.seat_limit > 0
                        ? (settings.seat_count / settings.seat_limit) * 100
                        : 0
                    )}%`,
                  }}
                />
              </div>
              <p className="mt-2 text-xs text-gray-500">
                {settings.seat_count >= settings.seat_limit
                  ? "You've reached your seat limit. Upgrade your plan to invite more teammates."
                  : `${settings.seat_limit - settings.seat_count} seat${
                      settings.seat_limit - settings.seat_count === 1 ? "" : "s"
                    } remaining on the ${settings.plan} plan.`}
              </p>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
