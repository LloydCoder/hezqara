import { AuthBridge } from "@/components/auth/AuthBridge";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const authConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  return <div className="min-h-screen bg-slate-50">{authConfigured ? <AuthBridge/> : null}<Sidebar authConfigured={authConfigured}/><main className="min-h-screen lg:ml-64">{children}</main></div>;
}
