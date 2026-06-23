import { cn } from "@/lib/utils";

/** ReachGTM brand mark — concentric "reach" rings hitting a target center,
 *  a nod to go-to-market targeting. Rendered in the brand blue. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("h-8 w-8", className)} aria-hidden>
      <rect width="32" height="32" rx="9" fill="var(--color-blue-600)" />
      <circle cx="16" cy="16" r="9" stroke="#fff" strokeOpacity="0.45" strokeWidth="1.6" />
      <circle cx="16" cy="16" r="5" stroke="#fff" strokeOpacity="0.7" strokeWidth="1.6" />
      <circle cx="16" cy="16" r="1.9" fill="#fff" />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <LogoMark className="h-7 w-7" />
      <span className="text-[1.0625rem] font-semibold tracking-tight text-ink">
        ReachGTM
      </span>
    </span>
  );
}
