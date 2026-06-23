"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Users, RefreshCw, AlertCircle } from "lucide-react";
import { teamApi } from "@/lib/api";
import { getRole, getUserId } from "@/lib/auth";
import { cn } from "@/lib/utils";
import type {
  AssignableRole,
  TeamMember,
  TeamRole,
  TeamSettings,
  WorkspacePlan,
} from "@/types";

const INVITABLE_ROLES: TeamRole[] = ["member", "admin"];

const PLANS: { value: WorkspacePlan; label: string }[] = [
  { value: "free", label: "Free" },
  { value: "pro", label: "Pro" },
  { value: "enterprise", label: "Enterprise" },
];

export default function TeamPage() {
  const [role, setRole] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [resolved, setResolved] = useState(false);

  const [inviteRole, setInviteRole] = useState<TeamRole>("member");
  const [inviteUrl, setInviteUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const [members, setMembers] = useState<TeamMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);
  const [pendingUserId, setPendingUserId] = useState<string | null>(null);

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
      // ignore
    }
  }

  if (!resolved) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
        <div className="skeleton h-8 w-40" />
        <div className="skeleton mt-6 h-40 w-full" />
      </main>
    );
  }

  if (!canInvite) {
    return (
      <main className="mx-auto max-w-3xl px-5 py-16 sm:px-8">
        <p className="eyebrow">Workspace</p>
        <h1 className="display mt-2.5 text-[2.5rem] font-medium leading-tight text-ink">
          Team
        </h1>
        <div className="alert alert-warn mt-7">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-semibold">You don&apos;t have access</p>
            <p className="opacity-80">
              Only workspace owners and admins can manage teammates. Ask an admin
              if you need access.
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8 sm:py-16">
      <header className="animate-rise mb-9">
        <p className="eyebrow">Workspace</p>
        <h1 className="display mt-2.5 text-[2.5rem] font-medium leading-tight text-ink">
          Team
        </h1>
        <p className="mt-2 text-[0.9375rem] text-ink-muted">
          Invite teammates and manage your ReachGTM workspace.
        </p>
      </header>

      {/* Invite a teammate */}
      <section className="card p-6 sm:p-7">
        <h2 className="text-[0.9375rem] font-semibold text-ink">Invite a teammate</h2>
        <p className="mt-1 text-[0.8125rem] text-ink-muted">
          Pick a role and generate a one-time invite link to share.
        </p>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="sm:w-48">
            <label className="field-label">Role</label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as TeamRole)}
              className="field capitalize"
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
            className="btn btn-flare"
          >
            {loading ? "Generating…" : "Generate invite link"}
          </button>
        </div>

        {error && <p className="mt-3 text-[0.8125rem] font-medium text-danger">{error}</p>}

        {inviteUrl && (
          <div className="mt-5">
            <label className="field-label">Invite link</label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={inviteUrl}
                onFocus={(e) => e.currentTarget.select()}
                className="field mono bg-sunken text-[0.8125rem]"
              />
              <button
                type="button"
                onClick={handleCopy}
                className="btn btn-secondary shrink-0"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-success" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <p className="mt-2 text-[0.75rem] text-ink-faint">
              Share this link with your teammate. They&apos;ll set their email and
              password to join.
            </p>
          </div>
        )}
      </section>

      {/* Members */}
      <section className="card mt-5 p-6 sm:p-7">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[0.9375rem] font-semibold text-ink">Members</h2>
            <p className="mt-1 text-[0.8125rem] text-ink-muted">
              {isOwner
                ? "Promote or demote teammates between member and admin."
                : "Everyone in your workspace."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadMembers()}
            disabled={membersLoading}
            className="btn btn-ghost px-2.5"
            aria-label="Refresh members"
          >
            <RefreshCw className={cn("h-4 w-4", membersLoading && "animate-spin")} />
          </button>
        </div>

        {membersError && (
          <p className="mt-3 text-[0.8125rem] font-medium text-danger">{membersError}</p>
        )}

        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-[0.875rem]">
            <thead>
              <tr className="border-b border-hairline">
                <th className="eyebrow pb-2.5 pr-4 font-medium">Email</th>
                <th className="eyebrow pb-2.5 pr-4 font-medium">Role</th>
                <th className="eyebrow pb-2.5 pr-4 font-medium">Status</th>
                {isOwner && (
                  <th className="eyebrow pb-2.5 text-right font-medium">Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {members.length === 0 && !membersLoading && (
                <tr>
                  <td colSpan={isOwner ? 4 : 3} className="py-4 text-ink-muted">
                    No members yet.
                  </td>
                </tr>
              )}
              {members.map((m) => {
                const isSelf = m.id === userId;
                const isOwnerRow = m.role === "owner";
                const showActions = isOwner && !isOwnerRow && !isSelf;
                const busy = pendingUserId === m.id;
                return (
                  <tr key={m.id} className="border-b border-hairline last:border-0">
                    <td className="py-3.5 pr-4 font-medium text-ink">
                      {m.email}
                      {isSelf && (
                        <span className="ml-2 text-[0.75rem] text-ink-faint">(you)</span>
                      )}
                    </td>
                    <td className="py-3.5 pr-4">
                      <span className="chip chip-ink capitalize">{m.role}</span>
                    </td>
                    <td className="py-3.5 pr-4">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 text-[0.75rem] font-semibold",
                          m.is_active ? "text-success" : "text-ink-faint"
                        )}
                      >
                        <span
                          className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            m.is_active ? "bg-success" : "bg-ink-faint"
                          )}
                        />
                        {m.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    {isOwner && (
                      <td className="py-3.5 text-right">
                        {showActions ? (
                          m.role === "member" ? (
                            <button
                              type="button"
                              onClick={() => void handleRoleChange(m, "admin")}
                              disabled={busy}
                              className="rounded-md border border-flare-200 bg-flare-50 px-3 py-1.5 text-[0.75rem] font-semibold text-flare-700 transition-colors hover:bg-flare-100 disabled:opacity-50"
                            >
                              {busy ? "Saving…" : "Promote to admin"}
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => void handleRoleChange(m, "member")}
                              disabled={busy}
                              className="rounded-md border border-hairline-strong px-3 py-1.5 text-[0.75rem] font-semibold text-ink-muted transition-colors hover:bg-sunken hover:text-ink disabled:opacity-50"
                            >
                              {busy ? "Saving…" : "Demote to member"}
                            </button>
                          )
                        ) : (
                          <span className="text-ink-faint">·</span>
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

      {/* Workspace settings */}
      <section className="card mt-5 p-6 sm:p-7">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[0.9375rem] font-semibold text-ink">
              Workspace settings
            </h2>
            <p className="mt-1 text-[0.8125rem] text-ink-muted">
              {isOwner
                ? "Manage your workspace name, plan, and seat usage."
                : "Your workspace plan and seat usage."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadSettings()}
            disabled={settingsLoading}
            className="btn btn-ghost px-2.5"
            aria-label="Refresh settings"
          >
            <RefreshCw className={cn("h-4 w-4", settingsLoading && "animate-spin")} />
          </button>
        </div>

        {settingsError && (
          <p className="mt-3 text-[0.8125rem] font-medium text-danger">{settingsError}</p>
        )}

        {!settings && settingsLoading && (
          <div className="skeleton mt-5 h-32 w-full" />
        )}

        {settings && (
          <div className="mt-6 space-y-7">
            {/* Workspace name */}
            <div>
              <label className="field-label">Workspace name</label>
              {isOwner ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    className="field max-w-sm"
                  />
                  <button
                    type="button"
                    onClick={() => void handleRenameWorkspace()}
                    disabled={
                      settingsSaving ||
                      !nameDraft.trim() ||
                      nameDraft.trim() === settings.name
                    }
                    className="btn btn-primary shrink-0"
                  >
                    {settingsSaving ? "Saving…" : "Save"}
                  </button>
                </div>
              ) : (
                <p className="text-[0.9375rem] font-semibold text-ink">{settings.name}</p>
              )}
            </div>

            {/* Plan */}
            <div>
              <label className="field-label">Plan</label>
              {isOwner ? (
                <select
                  value={settings.plan}
                  onChange={(e) => void handlePlanChange(e.target.value as WorkspacePlan)}
                  disabled={settingsSaving}
                  className="field max-w-sm capitalize"
                >
                  {PLANS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="chip chip-ink capitalize">{settings.plan}</span>
              )}
              {isOwner && (
                <p className="mt-2 text-[0.75rem] text-warn">
                  Billing isn&apos;t integrated yet — switching plans takes effect
                  immediately and doesn&apos;t charge a card.
                </p>
              )}
            </div>

            {/* Seat usage */}
            <div>
              <div className="flex items-center justify-between max-w-sm">
                <label className="field-label !mb-0">Seats</label>
                <span className="mono text-[0.8125rem] text-ink">
                  {settings.seat_count} / {settings.seat_limit}
                </span>
              </div>
              <div className="mt-2.5 h-2 w-full max-w-sm overflow-hidden rounded-full bg-sunken">
                <div
                  className={cn(
                    "h-full rounded-full",
                    settings.seat_count >= settings.seat_limit
                      ? "bg-danger"
                      : "bg-flare-600"
                  )}
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
              <p className="mt-2 text-[0.75rem] text-ink-faint">
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
