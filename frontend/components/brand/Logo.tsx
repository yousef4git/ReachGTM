import { cn } from "@/lib/utils";

/** ReachGTM mark — radiating arcs expanding from an origin point: "reach"
 *  growing outward (signal / expansion / momentum). Monochrome ink tile with
 *  white arcs; the arcs read clearly on dark surfaces too. No targeting motifs. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={cn("h-8 w-8", className)}
      aria-hidden
    >
      <rect width="32" height="32" rx="8" fill="var(--color-ink)" />
      {/* arcs radiate from the lower-left origin, brightest nearest the source */}
      <path
        d="M10 16 A6 6 0 0 1 16 22"
        stroke="#fff"
        strokeOpacity="0.95"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
      <path
        d="M10 11 A11 11 0 0 1 21 22"
        stroke="#fff"
        strokeOpacity="0.62"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
      <path
        d="M10 6 A16 16 0 0 1 26 22"
        stroke="#fff"
        strokeOpacity="0.32"
        strokeWidth="1.9"
        strokeLinecap="round"
      />
      <circle cx="10" cy="22" r="2.1" fill="#fff" />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark className="h-8 w-8" />
      <span className="text-[1.0625rem] font-semibold tracking-tight text-ink">
        Reach<span className="text-ink-muted">GTM</span>
      </span>
    </span>
  );
}
