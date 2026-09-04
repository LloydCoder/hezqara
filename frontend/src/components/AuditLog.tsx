"use client";

import { formatDateTime, maskPhone } from "@/lib/utils";

interface AuditEntry {
  id: string;
  event_type: string;
  clinic_id: string;
  call_id?: string;
  patient_id?: string;
  agent_type?: string;
  created_at: string;
}

interface AuditLogProps {
  entries: AuditEntry[];
  loading?: boolean;
}

const EVENT_ICONS: Record<string, string> = {
  call_started: "📞",
  call_ended: "📵",
  appointment_booked: "📅",
  intake_submitted: "📝",
  eligibility_checked: "🛡️",
  prior_auth_submitted: "📋",
  refill_processed: "💊",
  records_released: "📁",
  referral_created: "🔗",
  recall_sent: "📣",
  email_sent: "✉️",
};

export function AuditLog({ entries, loading }: AuditLogProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-12 bg-slate-100 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        No audit events yet
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className="flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
        >
          <span className="text-base w-6 text-center flex-shrink-0">
            {EVENT_ICONS[entry.event_type] ?? "•"}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-slate-700 capitalize">
              {entry.event_type.replace(/_/g, " ")}
            </p>
            <p className="text-xs text-slate-400 truncate">
              {entry.agent_type && `${entry.agent_type} agent`}
              {entry.patient_id && ` · patient ${entry.patient_id.slice(0, 8)}`}
            </p>
          </div>
          <p className="text-xs text-slate-400 flex-shrink-0">
            {formatDateTime(entry.created_at)}
          </p>
        </div>
      ))}
    </div>
  );
}
