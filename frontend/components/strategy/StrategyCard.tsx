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
    <div className={cn("rounded-xl border bg-white p-6 shadow-sm", className)}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {strategy.positioning_statement.slice(0, 80)}
            {strategy.positioning_statement.length > 80 ? "..." : ""}
          </h3>
          {strategy.icp && (
            <p className="mt-1 text-sm text-gray-500">
              {strategy.icp.title} · {strategy.icp.industry} · {strategy.icp.company_size}
            </p>
          )}
        </div>
        <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
          {motionLabels[strategy.motion] ?? strategy.motion}
        </span>
      </div>

      {strategy.icp && strategy.icp.pain_points.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Pain Points</p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {strategy.icp.pain_points.slice(0, 4).map((p, i) => (
              <span key={i} className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                {p}
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="mt-4 text-xs text-gray-400">
        Generated {new Date(strategy.generated_at).toLocaleDateString()}
      </p>
    </div>
  );
}
