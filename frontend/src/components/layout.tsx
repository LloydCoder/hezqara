import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Carenova AI — Medical Front Office",
  description: "AI-powered medical front office. Never miss another patient call.",
  icons: { icon: "/favicon.ico" },
  openGraph: {
    title: "Carenova AI",
    description: "AI Medical Front Office Platform",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        {/* ClerkProvider wraps at middleware level — see middleware.ts */}
        {/* This avoids SSR issues with Clerk on Next.js 15 */}
        {children}
      </body>
    </html>
  );
}
