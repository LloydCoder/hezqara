import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <img src="/brand/hezqara-logo-horizontal-full-color.svg" alt="HEZQARA" width={179} height={48} className="mx-auto h-10 w-auto" />
          <h1 className="mt-5 text-2xl font-bold text-slate-900">Start your free trial</h1>
          <p className="mt-1 text-sm text-slate-600">A governed AI workforce for healthcare front-office operations.</p>
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
    </div>
  );
}
