import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { isClerkConfigured } from "@/lib/clerk-config";
import "@/styles/brand.css";
import "./globals.css";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim() || "https://hezqara.vercel.app";
const socialImage = "/opengraph-image";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "HEZQARA — The governed AI workforce for healthcare", template: "%s — HEZQARA" },
  description: "A governed AI workforce for healthcare front-office operations, with human oversight and accountable execution.",
  applicationName: "HEZQARA",
  robots: { index: true, follow: true },
  manifest: "/site.webmanifest",
  openGraph: {
    type: "website",
    siteName: "HEZQARA",
    title: "HEZQARA — The governed AI workforce for healthcare",
    description: "A governed AI workforce for healthcare front-office operations.",
    url: siteUrl,
    images: [{ url: socialImage, width: 1200, height: 630, alt: "HEZQARA — The governed AI workforce for healthcare" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HEZQARA — The governed AI workforce for healthcare",
    description: "A governed AI workforce for healthcare front-office operations.",
    images: [socialImage],
  },
};

export const viewport: Viewport = {
  themeColor: "#0F2A47",
  colorScheme: "light",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const content = (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#0F2A47" />
      </head>
      <body>{children}</body>
    </html>
  );

  return publishableKey && isClerkConfigured()
    ? <ClerkProvider publishableKey={publishableKey} afterSignOutUrl="/">{content}</ClerkProvider>
    : content;
}
