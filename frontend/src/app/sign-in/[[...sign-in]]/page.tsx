import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
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

        {publishableKey ? (
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
        ) : (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900 shadow-sm">
            Authentication is not configured for this deployment. Set
            <code className="mx-1 rounded bg-amber-100 px-1.5 py-0.5">
              NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
            </code>
            before enabling sign-in.
          </div>
        )}
      </div>
    </div>
  );
}
