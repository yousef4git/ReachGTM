import { Wordmark } from "@/components/brand/Logo";

/** Centered, branded auth layout shared by sign-in and sign-up. */
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
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 py-12">
      {/* Soft ambient blobs: solid tints, blurred (no gradients). Gentle drift. */}
      <div
        aria-hidden
        className="auth-blob pointer-events-none absolute -top-32 left-1/2 h-[30rem] w-[30rem] -translate-x-1/2 rounded-full blur-[120px]"
        style={{ backgroundColor: "color-mix(in oklab, var(--color-blue-600) 12%, transparent)" }}
      />
      <div
        aria-hidden
        className="auth-blob-slow pointer-events-none absolute bottom-[-8rem] right-[-6rem] h-[24rem] w-[24rem] rounded-full blur-[120px]"
        style={{ backgroundColor: "color-mix(in oklab, var(--color-blue-400) 10%, transparent)" }}
      />

      <div className="animate-rise w-full max-w-[25rem]">
        <div className="mb-7 flex justify-center">
          <Wordmark />
        </div>

        <div className="card p-8 shadow-md">
          <header className="mb-6">
            <h1 className="text-[1.5rem] font-semibold tracking-tight text-ink">{title}</h1>
            {subtitle ? (
              <p className="mt-1.5 text-[0.9375rem] leading-relaxed text-ink-muted">{subtitle}</p>
            ) : null}
          </header>
          {children}
        </div>

        {footer ? (
          <p className="mt-6 text-center text-[0.875rem] text-ink-muted">{footer}</p>
        ) : null}
      </div>
    </main>
  );
}
