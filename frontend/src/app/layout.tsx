import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { isClerkConfigured } from "@/lib/clerk-config";
import "@/styles/brand.css";
import "./globals.css";

// Temporary production alias; override NEXT_PUBLIC_SITE_URL when the owned custom domain is attached.
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim() || "https://hezqara-yvj6.vercel.app";
const socialImage = "/opengraph-image.svg";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "HEZQARA — The governed AI workforce for healthcare", template: "%s — HEZQARA" },
  description: "A governed AI workforce for healthcare front-office operations, with human oversight and accountable execution.",
  alternates: { canonical: siteUrl },
  applicationName: "HEZQARA",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }, { url: "/favicon.ico", sizes: "48x48" }],
    shortcut: ["/favicon.ico"],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
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
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
        <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#0F2A47" />
      </head>
      <body>{children}</body>
    </html>
  );

  return publishableKey && isClerkConfigured()
    ? <ClerkProvider publishableKey={publishableKey} afterSignOutUrl="/">{content}</ClerkProvider>
    : content;
}
