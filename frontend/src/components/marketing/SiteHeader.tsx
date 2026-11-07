import type { Route } from "next";
import Link from "next/link";
import { SiteMobileNav } from "@/components/marketing/SiteMobileNav";
import { siteNavigation } from "@/components/marketing/site-navigation";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 sm:h-20 sm:px-8">
        <Link href={"/" as Route} className="flex shrink-0 items-center" aria-label="HEZQARA home">
          <picture>
            <source media="(min-width: 640px)" srcSet="/brand/hezqara-logo-horizontal-tagline-full-color.svg" />
            <img src="/brand/hezqara-logo-horizontal-full-color.svg" alt="HEZQARA" width={179} height={48} className="h-10 w-auto sm:h-[70px]" />
          </picture>
        </Link>
        <nav className="hidden items-center gap-6 lg:flex" aria-label="Primary navigation">
          {siteNavigation.map(([label, href]) => (
            <Link key={href} href={href as Route} className="text-sm font-medium text-slate-600 transition hover:text-slate-950">
              {label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <Link href={"/sign-in" as Route} className="hidden rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 sm:inline-flex">Sign in</Link>
          <Link href={"/sign-up" as Route} className="inline-flex rounded-lg bg-slate-950 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-hz-teal-deep focus:ring-offset-2 max-[360px]:hidden sm:px-4">See HEZQARA</Link>
          <SiteMobileNav />
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-12 sm:px-8 md:grid-cols-4">
        <div className="md:col-span-2">
          <img src="/brand/hezqara-logo-horizontal-tagline-full-color.svg" alt="HEZQARA" width={358} height={96} className="h-auto w-[260px] max-w-full" />
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-600">A governed AI workforce for healthcare front-office operations.</p>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-950">Explore</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            <Link className="block hover:text-slate-950" href={"/product" as Route}>Product</Link>
            <Link className="block hover:text-slate-950" href={"/workforce" as Route}>AI workforce</Link>
            <Link className="block hover:text-slate-950" href={"/solutions" as Route}>Solutions</Link>
            <Link className="block hover:text-slate-950" href={"/pricing" as Route}>Pricing</Link>
          </div>
        </div>
        <div>
          <h2 className="text-sm font-semibold text-slate-950">Trust</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            <Link className="block hover:text-slate-950" href={"/security" as Route}>Security</Link>
            <Link className="block hover:text-slate-950" href={"/compliance" as Route}>Compliance</Link>
            <Link className="block hover:text-slate-950" href={"/enterprise" as Route}>Enterprise</Link>
            <Link className="block hover:text-slate-950" href={"/contact" as Route}>Contact</Link>
          </div>
        </div>
      </div>
      <div className="border-t border-slate-100 px-5 py-5 text-center text-xs text-slate-500">© {new Date().getFullYear()} HEZQARA. Administrative workflow automation for healthcare.</div>
    </footer>
  );
}
