import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata:Metadata={title:{default:"HEZQARA — AI Workforce for Healthcare",template:"%s — HEZQARA"},description:"AI workforce infrastructure for healthcare operations, with governed automation, human escalation, and accountable execution.",applicationName:"HEZQARA",robots:{index:true,follow:true},openGraph:{type:"website",siteName:"HEZQARA",title:"HEZQARA — AI Workforce for Healthcare",description:"Governed AI workforce infrastructure for healthcare operations."},twitter:{card:"summary_large_image",title:"HEZQARA — AI Workforce for Healthcare",description:"Governed AI workforce infrastructure for healthcare operations."}};

export default function RootLayout({children}:{children:React.ReactNode}){const publishableKey=process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;const content=<html lang="en" suppressHydrationWarning><body>{children}</body></html>;return publishableKey?<ClerkProvider publishableKey={publishableKey}>{content}</ClerkProvider>:content;}
