import { Wordmark, LogoMark } from "@/components/brand/Logo";
import { Search, Compass, FileText, ShieldCheck } from "lucide-react";

const STORY = [
  { icon: Search, label: "Research", blurb: "Grounded in the live web + your docs" },
  { icon: Compass, label: "Strategy", blurb: "ICP, positioning, and motion" },
  { icon: FileText, label: "Content", blurb: "Emails, posts, ads — on brand" },
  { icon: ShieldCheck, label: "Brand check", blurb: "Every asset scored for voice" },
];

/** Split-screen auth: an ink "command desk" story panel beside the form. */
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col lg:flex-row">
      {/* ── Story panel (ink) ────────────────────────────────────────────── */}
      <aside className="relative hidden overflow-hidden bg-ink px-12 py-14 text-canvas lg:flex lg:w-[44%] lg:flex-col lg:justify-between">
        {/* ambient signal blob — solid tint, blurred (no gradient) */}
        <div
          aria-hidden
          className="auth-blob pointer-events-none absolute -right-24 top-10 h-[26rem] w-[26rem] rounded-full blur-[130px]"
          style={{ backgroundColor: "color-mix(in oklab, var(--color-flare-600) 30%, transparent)" }}
        />
        <div className="relative">
          <span className="flex items-center gap-2.5">
            <LogoMark className="h-9 w-9" />
            <span className="text-[1.125rem] font-semibold tracking-tight">
              Reach<span className="text-canvas/55">GTM</span>
            </span>
          </span>
        </div>

        <div className="relative max-w-md">
          <p className="eyebrow !text-flare-400">GTM Command Desk</p>
          <h2 className="display mt-4 text-[2.5rem] font-medium leading-[1.05]">
            Go-to-market, on autopilot.
          </h2>
          <p className="mt-4 text-[0.9375rem] leading-relaxed text-canvas/60">
            A team of specialist agents researches your market, builds the
            strategy, and writes the content — in minutes, not weeks.
          </p>

          <ul className="mt-9 space-y-3.5">
            {STORY.map((s) => (
              <li key={s.label} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.05]">
                  <s.icon className="h-4 w-4 text-flare-400" strokeWidth={1.75} />
                </span>
                <div>
                  <p className="text-[0.875rem] font-semibold">{s.label}</p>
                  <p className="text-[0.8125rem] text-canvas/45">{s.blurb}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="eyebrow relative !text-canvas/35">
          Research · Strategy · Content · Brand
        </p>
      </aside>

      {/* ── Form ─────────────────────────────────────────────────────────── */}
      <section className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="animate-rise w-full max-w-[25rem]">
          <div className="mb-8 flex justify-center lg:hidden">
            <Wordmark />
          </div>

          <header className="mb-7">
            <h1 className="display text-[2rem] font-medium leading-tight tracking-tight text-ink">
              {title}
            </h1>
            {subtitle ? (
              <p className="mt-2 text-[0.9375rem] leading-relaxed text-ink-muted">
                {subtitle}
              </p>
            ) : null}
          </header>

          {children}

          {footer ? (
            <p className="mt-7 text-center text-[0.875rem] text-ink-muted">
              {footer}
            </p>
          ) : null}
        </div>
      </section>
    </main>
  );
}
