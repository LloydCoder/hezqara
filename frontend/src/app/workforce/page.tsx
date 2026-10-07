import type { Route } from "next";
import Link from "next/link";
import { MarketingShell, SectionIntro } from "@/components/marketing/MarketingShell";

const agents = [
  ["reception", "Reception Agent", "Handles structured front-office requests and routes exceptions."],
  ["scheduling", "Scheduling Agent", "Coordinates eligible scheduling workflows and availability requests."],
  ["intake", "Intake Agent", "Organizes administrative intake information for downstream workflows."],
  ["insurance", "Insurance Agent", "Supports insurance verification and administrative follow-up."],
  ["insurance-administrative", "Insurance Administrative Agent", "Supports payer administration and coverage workflow coordination."],
  ["prior-authorization", "Prior Authorization Agent", "Coordinates authorization preparation, status, and follow-up workflows."],
  ["revenue-cycle", "Revenue Cycle Agent", "Coordinates governed claims and revenue-cycle operations."],
  ["records", "Records Agent", "Supports records-request coordination and status management."],
  ["referrals", "Referrals Agent", "Coordinates referral intake, routing, and follow-up."],
  ["referral-records", "Referral Records Agent", "Coordinates referral documentation and record workflows."],
  ["refill", "Refill Agent", "Routes eligible refill administration while escalating consequential requests."],
  ["recall", "Recall Agent", "Supports recall and governed follow-up outreach workflows."],
  ["email", "Email Agent", "Drafts and coordinates operational email workflows within policy boundaries."],
] as const;

export default function WorkforcePage() {
  return (
    <MarketingShell>
      <main>
        <section className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-24">
          <SectionIntro
            eyebrow="AI workforce"
            title="Thirteen specialized workers. One governed operating model."
            body="HEZQARA is designed as a coordinated workforce rather than a single general-purpose chatbot. Each worker has a defined operational role, permission boundary, owning enterprise phase, and escalation path."
          />
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map(([slug, name, body]) => (
              <Link
                key={slug}
                href={`/workforce/${slug}` as Route}
                className="group rounded-2xl border border-slate-200 p-6 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg"
              >
                <div className="flex items-center justify-between">
                  <span className="h-9 w-9 rounded-xl bg-slate-100" />
                  <span className="text-xs font-semibold text-slate-400">Agent</span>
                </div>
                <h2 className="mt-7 text-lg font-bold">{name}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
                <span className="mt-5 inline-flex text-sm font-semibold text-slate-950">Explore role →</span>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </MarketingShell>
  );
}
