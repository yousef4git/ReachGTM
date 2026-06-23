"use client";

import { useMemo } from "react";
import Link from "next/link";
import { CopyButton } from "@/components/ui/CopyButton";
import { cn } from "@/lib/utils";
import type { StrategyBundle, GTMStrategy, ContentAsset } from "@/types";
import { GTMMotion } from "@/types";
import {
  Target,
  Compass,
  Megaphone,
  CalendarRange,
  Repeat,
  Sparkles,
  ArrowRight,
  Library,
  Download,
  FileText,
  MessageCircle,
  Newspaper,
} from "lucide-react";

const MOTION_LABELS: Record<string, string> = {
  [GTMMotion.PLG]: "Product-led growth",
  [GTMMotion.SLG]: "Sales-led growth",
  [GTMMotion.CLG]: "Community-led growth",
  [GTMMotion.MLG]: "Marketing-led growth",
};

const CONTENT_META: Record<string, { label: string; icon: React.ReactNode }> = {
  cold_email: { label: "Cold email", icon: <FileText className="h-3.5 w-3.5" /> },
  linkedin_post: { label: "LinkedIn", icon: <MessageCircle className="h-3.5 w-3.5" /> },
  blog_outline: { label: "Blog outline", icon: <Newspaper className="h-3.5 w-3.5" /> },
  ad_copy: { label: "Ad copy", icon: <Megaphone className="h-3.5 w-3.5" /> },
};

function strategyToMarkdown(s: GTMStrategy, assets: ContentAsset[], company: string): string {
  const lines: string[] = [`# GTM Strategy — ${company}`, ""];
  lines.push(`**Motion:** ${MOTION_LABELS[s.motion] ?? s.motion}`, "");
  lines.push(`> ${s.positioning_statement}`, "");
  if (s.value_proposition) {
    lines.push(`## Value proposition`, `**${s.value_proposition.headline}**`, s.value_proposition.subheadline, "");
    s.value_proposition.proof_points?.forEach((p) => lines.push(`- ${p}`));
    lines.push("");
  }
  if (s.channels?.length) {
    lines.push(`## Channels`);
    s.channels.forEach((c) => lines.push(`${c.priority}. **${c.name}** — ${c.rationale}`));
    lines.push("");
  }
  if (s.ninety_day_plan?.length) {
    lines.push(`## 90-day plan`);
    s.ninety_day_plan.forEach((m) => lines.push(`- **Week ${m.week}** (${m.owner}): ${m.goal}`));
    lines.push("");
  }
  if (assets.length) {
    lines.push(`## Content assets`);
    assets.forEach((a) => lines.push(`### ${CONTENT_META[a.type]?.label ?? a.type}: ${a.title}`, a.body, ""));
  }
  return lines.join("\n");
}

interface StrategyResultProps {
  bundle: StrategyBundle;
  companyName: string;
}

export function StrategyResult({ bundle, companyName }: StrategyResultProps) {
  const s = bundle.gtm_strategy;
  const assets = bundle.content_assets ?? [];
  const research = bundle.research_report;

  const markdown = useMemo(
    () => (s ? strategyToMarkdown(s, assets, companyName) : ""),
    [s, assets, companyName]
  );

  const onDownload = () => {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gtm-strategy-${companyName.toLowerCase().replace(/\s+/g, "-")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* ── Completion summary + actions ─────────────────────────────── */}
      <div className="animate-rise card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-hairline bg-sunken px-6 py-5">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-success)] text-canvas">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <p className="eyebrow">Deliverable ready</p>
              <h2 className="display text-[1.375rem] font-medium leading-tight text-ink">
                {companyName}&apos;s go-to-market plan
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {markdown && <CopyButton text={markdown} label="Copy all" />}
            <button onClick={onDownload} className="btn btn-secondary !px-3 !py-2 text-[0.75rem]">
              <Download className="h-3.5 w-3.5" />
              Export .md
            </button>
          </div>
        </div>

        {/* stat strip */}
        <div className="grid grid-cols-2 divide-x divide-hairline sm:grid-cols-4">
          <Stat label="Motion" value={s ? (MOTION_LABELS[s.motion] ?? s.motion).split(" ")[0] : "—"} />
          <Stat label="Channels" value={String(s?.channels?.length ?? 0)} />
          <Stat label="Content" value={String(assets.length)} />
          <Stat label="Plan" value={`${s?.ninety_day_plan?.length ?? 0} wk`} />
        </div>

        {/* where it lives */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 border-t border-hairline px-6 py-3.5 text-[0.8125rem] text-ink-muted">
          <Library className="h-4 w-4 text-flare-600" />
          <span>
            {assets.length > 0 ? (
              <>
                {assets.length} asset{assets.length === 1 ? "" : "s"} saved to your
              </>
            ) : (
              "Find everything in your"
            )}
          </span>
          <Link href="/content" className="font-semibold text-ink underline-offset-2 hover:underline">
            Content library
          </Link>
          <ArrowRight className="h-3.5 w-3.5 text-ink-faint" />
        </div>
      </div>

      {!s && (
        <p className="text-[0.875rem] text-ink-muted">
          The strategy payload wasn&apos;t returned. Check the event log below.
        </p>
      )}

      {s && (
        <>
          {/* ── Positioning hero ───────────────────────────────────────── */}
          <section className="animate-rise card p-7 sm:p-9" style={{ animationDelay: "60ms" }}>
            <div className="flex items-center justify-between gap-3">
              <p className="eyebrow">Positioning</p>
              <span className="chip chip-flare">
                <Compass className="h-3.5 w-3.5" />
                {MOTION_LABELS[s.motion] ?? s.motion}
              </span>
            </div>
            <p className="display mt-4 text-[1.625rem] font-normal leading-snug text-ink sm:text-[1.875rem]">
              {s.positioning_statement}
            </p>
          </section>

          {/* ── Value proposition ──────────────────────────────────────── */}
          {s.value_proposition && (
            <Section icon={<Target className="h-4 w-4" />} title="Value proposition" delay={120}>
              <h3 className="display text-[1.25rem] font-medium text-ink">
                {s.value_proposition.headline}
              </h3>
              <p className="mt-1.5 text-[0.9375rem] text-ink-muted">
                {s.value_proposition.subheadline}
              </p>
              {s.value_proposition.proof_points?.length > 0 && (
                <ul className="mt-4 grid gap-2 sm:grid-cols-2">
                  {s.value_proposition.proof_points.map((p, i) => (
                    <li key={i} className="flex gap-2 text-[0.875rem] text-ink">
                      <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-flare-600" />
                      {p}
                    </li>
                  ))}
                </ul>
              )}
              {s.value_proposition.differentiators?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {s.value_proposition.differentiators.map((d, i) => (
                    <span key={i} className="chip chip-ink">{d}</span>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* ── ICP ────────────────────────────────────────────────────── */}
          {s.icp && (
            <Section icon={<Target className="h-4 w-4" />} title="Ideal customer profile" delay={180}>
              <div className="grid gap-5 sm:grid-cols-3">
                <Field label="Title" value={s.icp.title} />
                <Field label="Industry" value={s.icp.industry} />
                <Field label="Company size" value={s.icp.company_size} />
              </div>
              {s.icp.pain_points?.length > 0 && (
                <div className="mt-5">
                  <p className="eyebrow">Pain points</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {s.icp.pain_points.map((p, i) => (
                      <span key={i} className="chip chip-ink">{p}</span>
                    ))}
                  </div>
                </div>
              )}
            </Section>
          )}

          {/* ── Channels ───────────────────────────────────────────────── */}
          {s.channels && s.channels.length > 0 && (
            <Section icon={<Megaphone className="h-4 w-4" />} title="Channel plan" delay={240}>
              <div className="space-y-3">
                {[...s.channels].sort((a, b) => a.priority - b.priority).map((c, i) => (
                  <div key={i} className="flex gap-4 rounded-xl border border-hairline bg-sunken/40 p-4">
                    <span className="mono grid h-7 w-7 shrink-0 place-items-center rounded-full bg-ink text-[0.75rem] font-semibold text-canvas">
                      {c.priority}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h4 className="text-[0.9375rem] font-semibold capitalize text-ink">
                          {c.name.replace(/_/g, " ")}
                        </h4>
                        {c.estimated_cac && (
                          <span className="mono text-[0.6875rem] text-ink-faint">CAC {c.estimated_cac}</span>
                        )}
                      </div>
                      <p className="mt-1 text-[0.875rem] text-ink-muted">{c.rationale}</p>
                      {c.kpis?.length > 0 && (
                        <div className="mt-2.5 flex flex-wrap gap-1.5">
                          {c.kpis.map((k, j) => (
                            <span key={j} className="rounded-md bg-surface px-2 py-0.5 text-[0.6875rem] font-medium text-ink-muted ring-1 ring-hairline">
                              {k}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* ── 90-day plan ────────────────────────────────────────────── */}
          {s.ninety_day_plan && s.ninety_day_plan.length > 0 && (
            <Section icon={<CalendarRange className="h-4 w-4" />} title="90-day plan" delay={300}>
              <ol className="relative space-y-5 before:absolute before:left-[7px] before:top-1.5 before:h-[calc(100%-12px)] before:w-px before:bg-hairline">
                {[...s.ninety_day_plan].sort((a, b) => a.week - b.week).map((m, i) => (
                  <li key={i} className="relative pl-7">
                    <span className="absolute left-0 top-1 h-3.5 w-3.5 rounded-full border-2 border-flare-600 bg-canvas" />
                    <div className="flex flex-wrap items-baseline gap-x-2">
                      <span className="mono text-[0.6875rem] font-semibold text-flare-600">WEEK {m.week}</span>
                      <span className="mono text-[0.6875rem] text-ink-faint">· {m.owner}</span>
                    </div>
                    <p className="mt-0.5 text-[0.9375rem] text-ink">{m.goal}</p>
                    {m.kpis?.length > 0 && (
                      <p className="mt-1 text-[0.8125rem] text-ink-muted">{m.kpis.join(" · ")}</p>
                    )}
                  </li>
                ))}
              </ol>
            </Section>
          )}

          {/* ── Growth loops ───────────────────────────────────────────── */}
          {s.growth_loops && s.growth_loops.length > 0 && (
            <Section icon={<Repeat className="h-4 w-4" />} title="Growth loops" delay={360}>
              <div className="grid gap-3 sm:grid-cols-2">
                {s.growth_loops.map((g, i) => (
                  <div key={i} className="rounded-xl border border-hairline bg-sunken/40 p-4">
                    <div className="flex items-center justify-between">
                      <h4 className="text-[0.9375rem] font-semibold text-ink">{g.name}</h4>
                      <span className="chip chip-ink capitalize">{g.type}</span>
                    </div>
                    <p className="mt-1.5 text-[0.875rem] text-ink-muted">{g.description}</p>
                    <p className="mono mt-2.5 text-[0.6875rem] text-ink-faint">
                      {g.input_metric} → {g.output_metric}
                    </p>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </>
      )}

      {/* ── Content assets ───────────────────────────────────────────── */}
      {assets.length > 0 && (
        <Section icon={<Sparkles className="h-4 w-4" />} title={`Content assets · ${assets.length}`} delay={420}>
          <div className="space-y-3">
            {assets.map((a) => {
              const meta = CONTENT_META[a.type] ?? { label: a.type, icon: <FileText className="h-3.5 w-3.5" /> };
              return (
                <div key={a.id} className="rounded-xl border border-hairline bg-surface p-4 transition-shadow hover:shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <span className="chip chip-flare mb-2">{meta.icon}{meta.label}</span>
                      <h4 className="text-[0.9375rem] font-semibold leading-snug text-ink">{a.title}</h4>
                    </div>
                    <CopyButton text={`${a.title}\n\n${a.body}`} />
                  </div>
                  <p className="mt-2 whitespace-pre-wrap text-[0.875rem] leading-relaxed text-ink-muted line-clamp-[8]">
                    {a.body}
                  </p>
                  {typeof a.brand_alignment_score === "number" && (
                    <p className="mono mt-3 text-[0.6875rem] text-ink-faint">
                      Brand alignment {Math.round(a.brand_alignment_score * 100)}%
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* ── Research grounding ───────────────────────────────────────── */}
      {research && (research.competitors?.length || research.sources?.length) && (
        <Section icon={<FileText className="h-4 w-4" />} title="Research grounding" delay={480}>
          {research.competitors && research.competitors.length > 0 && (
            <div className="mb-4">
              <p className="eyebrow">Competitors mapped</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {research.competitors.map((c, i) => (
                  <span key={i} className="chip chip-ink">{c.name}</span>
                ))}
              </div>
            </div>
          )}
          {research.sources && research.sources.length > 0 && (
            <p className="mono text-[0.6875rem] text-ink-faint">
              Grounded on {research.sources.length} source{research.sources.length === 1 ? "" : "s"}
            </p>
          )}
        </Section>
      )}

      {/* ── Next actions ─────────────────────────────────────────────── */}
      <div className="animate-rise flex flex-col gap-3 sm:flex-row" style={{ animationDelay: "540ms" }}>
        <Link href="/content" className="btn btn-flare flex-1 justify-center">
          <Library className="h-4 w-4" />
          Open content library
        </Link>
        <Link href="/strategy/new" className="btn btn-secondary flex-1 justify-center">
          <Sparkles className="h-4 w-4" />
          New strategy
        </Link>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-5 py-4">
      <p className="eyebrow">{label}</p>
      <p className="display mt-1 text-[1.25rem] font-medium capitalize text-ink">{value}</p>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className="mt-1 text-[0.9375rem] font-semibold text-ink">{value}</p>
    </div>
  );
}

function Section({
  icon,
  title,
  delay,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  delay: number;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("animate-rise card p-6 sm:p-7")} style={{ animationDelay: `${delay}ms` }}>
      <div className="flex items-center gap-2 text-flare-600">
        {icon}
        <h3 className="text-[0.9375rem] font-semibold text-ink">{title}</h3>
      </div>
      <div className="rule mt-4 mb-5" />
      {children}
    </section>
  );
}
