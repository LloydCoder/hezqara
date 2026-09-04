import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Hezqara — AI Workforce for Healthcare",
  description:
    "AI-powered healthcare front-office and administrative workflow automation.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const content = (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );

  // Clerk is required for authenticated production traffic, but keeping the
  // provider conditional makes static/build validation deterministic when CI
  // intentionally has no tenant/auth secrets. The protected proxy remains the
  // runtime authorization boundary.
  return publishableKey ? (
    <ClerkProvider publishableKey={publishableKey}>{content}</ClerkProvider>
  ) : (
    content
  );
}
