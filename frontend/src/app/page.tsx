import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-emerald-500 rounded-xl mb-4">
            <span className="text-white font-bold text-lg">H</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Start your free trial</h1>
          <p className="text-slate-500 text-sm mt-1">Put your healthcare front office on autopilot.</p>
        </div>
        <SignUp
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "shadow-sm border border-slate-200 rounded-2xl",
              headerTitle: "hidden",
              headerSubtitle: "hidden",
            },
          }}
        />
      </div>
    </main>
  );
}
