import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500">
            <span className="text-lg font-bold text-white">H</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Hezqara</h1>
          <p className="mt-1 text-sm text-slate-500">
            Sign in to your healthcare operations workspace
          </p>
        </div>
        <SignIn
          appearance={{
            elements: {
              rootBox: "w-full",
              card: "rounded-2xl border border-slate-200 shadow-sm",
              headerTitle: "hidden",
              headerSubtitle: "hidden",
            },
          }}
        />
      </div>
    </div>
  );
}
