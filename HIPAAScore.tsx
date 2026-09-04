"use client";

interface HIPAACheck {
  label: string;
  status: "pass" | "pending" | "fail";
  detail?: string;
}

interface HIPAAScoreProps {
  checks: HIPAACheck[];
}

export function HIPAAScore({ checks }: HIPAAScoreProps) {
  const passing = checks.filter(c => c.status === "pass").length;
  const score = Math.round((passing / checks.length) * 100);

  const color =
    score >= 90 ? "text-emerald-600" :
    score >= 70 ? "text-amber-600" :
    "text-red-500";

  const barColor =
    score >= 90 ? "bg-emerald-500" :
    score >= 70 ? "bg-amber-500" :
    "bg-red-500";

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-700">HIPAA Compliance Score</h3>
          <p className="text-xs text-slate-400 mt-0.5">{passing} of {checks.length} controls passing</p>
        </div>
        <span className={`text-3xl font-bold tabular-nums ${color}`}>{score}%</span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Checks list */}
      <div className="divide-y divide-slate-50 -mx-6 px-6">
        {checks.map((check) => (
          <div key={check.label} className="flex items-center justify-between py-3">
            <div>
              <p className="text-sm text-slate-700">{check.label}</p>
              {check.detail && (
                <p className="text-xs text-slate-400 mt-0.5">{check.detail}</p>
              )}
            </div>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              check.status === "pass" ? "bg-emerald-50 text-emerald-700" :
              check.status === "pending" ? "bg-amber-50 text-amber-700" :
              "bg-red-50 text-red-600"
            }`}>
              {check.status === "pass" ? "✓ Pass" : check.status === "pending" ? "Pending" : "✗ Fail"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
