import { AuthBridge } from "@/components/auth/AuthBridge";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950">
      <AuthBridge />
      <Sidebar />
      <main className="min-h-screen lg:ml-56">{children}</main>
    </div>
  );
}
