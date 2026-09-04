import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen" style={{ background: "#0B1120" }}>
      <Sidebar />
      <main className="ml-56 min-h-screen">
        {children}
      </main>
    </div>
  );
}
