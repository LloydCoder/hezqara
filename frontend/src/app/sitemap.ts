import type { MetadataRoute } from "next";

const pages = [
  "/",
  "/product",
  "/workforce",
  "/solutions",
  "/solutions/billing",
  "/solutions/insurance",
  "/solutions/patient-engagement",
  "/solutions/operations",
  "/solutions/compliance",
  "/how-it-works",
  "/security",
  "/enterprise",
  "/pricing",
  "/contact",
  "/sign-in",
  "/sign-up",
];

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://hezqara.vercel.app";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl.replace(/\/$/, "");

  return pages.map((path) => ({
    url: `${base}${path}`,
    changeFrequency: path === "/" ? "weekly" : "monthly",
    priority:
      path === "/"
        ? 1
        : path.startsWith("/solutions") || path === "/workforce"
          ? 0.8
          : 0.6,
  }));
}
