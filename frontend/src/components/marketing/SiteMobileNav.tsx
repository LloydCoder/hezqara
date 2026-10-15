"use client";

import type { Route } from "next";
import Link from "next/link";
import { siteNavigation } from "@/components/marketing/site-navigation";

function closeMobileMenu() {
  document.getElementById("mobile-primary-navigation")?.hidePopover();
}

export function SiteMobileNav() {
  return (
    <>
      <button
        type="button"
        popoverTarget="mobile-primary-navigation"
        popoverTargetAction="toggle"
        aria-label="Toggle navigation menu"
        aria-controls="mobile-primary-navigation"
        className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2 lg:hidden"
      >
        <svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          <path d="M3 5h14M3 10h14M3 15h14" />
        </svg>
        <span>Menu</span>
      </button>

      <nav
        id="mobile-primary-navigation"
        popover="auto"
        aria-label="Mobile primary navigation"
        className="fixed inset-x-0 top-16 m-0 w-full max-w-none border-b border-slate-200 bg-white/95 px-5 py-4 shadow-lg backdrop-blur"
      >
        <ul className="mx-auto grid max-w-7xl gap-1 sm:grid-cols-2">
          {siteNavigation.map(([label, href]) => (
            <li key={href}>
              <Link
                href={href as Route}
                onClick={closeMobileMenu}
                className="flex min-h-11 items-center rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-inset"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
        <div className="mx-auto mt-3 grid max-w-7xl gap-2 border-t border-slate-200 pt-3 sm:grid-cols-2">
          <Link
            href={"/sign-in" as Route}
            onClick={closeMobileMenu}
            className="flex min-h-11 items-center justify-center rounded-lg border border-slate-200 px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
          >
            Sign in
          </Link>
          <Link
            href={"/sign-up" as Route}
            onClick={closeMobileMenu}
            className="flex min-h-11 items-center justify-center rounded-lg bg-slate-950 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
          >
            Get started
          </Link>
        </div>
      </nav>
    </>
  );
}
