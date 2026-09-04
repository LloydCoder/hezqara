import { cn } from "@/lib/utils";

interface MetricCardProps {
  label: string;
  value: string | number;
  subvalue?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  className?: string;
}

export function MetricCard({
  label,
  value,
  subvalue,
  trend,
  trendValue,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-5",
        className
      )}
    >
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      {subvalue && (
        <p className="mt-0.5 text-sm text-slate-500">{subvalue}</p>
      )}
      {trend && trendValue && (
        <div className="mt-3 flex items-center gap-1">
          <span
            className={cn(
              "text-xs font-medium",
              trend === "up" && "text-emerald-600",
              trend === "down" && "text-red-500",
              trend === "neutral" && "text-slate-500"
            )}
          >
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}{" "}
            {trendValue}
          </span>
          <span className="text-xs text-slate-400">vs yesterday</span>
        </div>
      )}
    </div>
  );
}
