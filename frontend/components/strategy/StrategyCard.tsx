import type { GTMStrategy } from "@/types";
import { cn } from "@/lib/utils";

interface StrategyCardProps {
  strategy: GTMStrategy;
  className?: string;
}

const motionLabels: Record<string, string> = {
  product_led_growth: "PLG",
  sales_led_growth: "SLG",
  community_led_growth: "CLG",
  marketing_led_growth: "MLG",
};

export function StrategyCard({ strategy, className }: StrategyCardProps) {
  return (
    <div className={cn("card overflow-hidden", className)}>
      {/* ink header strip with the motion badge */}
      <div className="flex items-start justify-between gap-4 border-b border-hairline bg-sunken px-6 py-5">
        <div className="min-w-0">
          <p className="eyebrow">Positioning</p>
          <h3 className="display mt-1.5 text-[1.25rem] font-medium leading-snug text-ink">
            {strategy.positioning_statement.slice(0, 96)}
            {strategy.positioning_statement.length > 96 ? "…" : ""}
          </h3>
          {strategy.icp && (
            <p className="mt-2 text-[0.8125rem] text-ink-muted">
              {strategy.icp.title} · {strategy.icp.industry} ·{" "}
              {strategy.icp.company_size}
            </p>
          )}
        </div>
        <span className="chip chip-flare shrink-0">
          {motionLabels[strategy.motion] ?? strategy.motion}
        </span>
      </div>

      <div className="px-6 py-5">
        {strategy.icp && strategy.icp.pain_points.length > 0 && (
          <div>
            <p className="eyebrow">Pain points</p>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {strategy.icp.pain_points.slice(0, 4).map((p, i) => (
                <span key={i} className="chip chip-ink">
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        <p className="mono mt-5 text-[0.6875rem] text-ink-faint">
          Generated {new Date(strategy.generated_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}
