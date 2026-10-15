"use client";

import type { Route } from "next";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { siteNavigation } from "@/components/marketing/site-navigation";

export function SiteMobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  function closeMenu() {
    setIsOpen(false);
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={isOpen}
        aria-controls="mobile-primary-navigation"
        onClick={() => setIsOpen((open) => !open)}
        className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2 lg:hidden"
      >
        <svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className="h-4 w-4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
          {isOpen ? <path d="m5 5 10 10M15 5 5 15" /> : <path d="M3 5h14M3 10h14M3 15h14" />}
        </svg>
        <span>{isOpen ? "Close" : "Menu"}</span>
      </button>

      <nav
        id="mobile-primary-navigation"
        aria-label="Mobile primary navigation"
        hidden={!isOpen}
        className="absolute inset-x-0 top-full border-b border-slate-200 bg-white/95 px-5 py-4 shadow-lg backdrop-blur lg:hidden"
      >
        <ul className="mx-auto grid max-w-7xl gap-1 sm:grid-cols-2">
          {siteNavigation.map(([label, href]) => (
            <li key={href}>
              <Link
                href={href as Route}
                onClick={closeMenu}
                className="flex min-h-11 items-center rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-inset"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
