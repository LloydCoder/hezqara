import { AuthBridge } from "@/components/auth/AuthBridge";
import { Sidebar } from "@/components/layout/Sidebar";
import { isClerkConfigured } from "@/lib/clerk-config";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  // Keep every Clerk hook consumer behind the exact same guard as ClerkProvider.
  // A present test key in production must not mount AuthBridge without its provider.
  const authConfigured = isClerkConfigured();
  return <div className="min-h-screen bg-slate-50">{authConfigured ? <AuthBridge/> : null}<Sidebar authConfigured={authConfigured}/><main className="min-h-screen lg:ml-64">{children}</main></div>;
}
