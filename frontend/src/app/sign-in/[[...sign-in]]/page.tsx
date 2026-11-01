import { SignIn } from "@clerk/nextjs";
import { isClerkConfigured } from "@/lib/clerk-config";

export default function SignInPage() {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const authenticationConfigured = Boolean(publishableKey) && isClerkConfigured();

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-7 text-center text-white">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-white text-sm font-black text-slate-950">H</div>
          <h1 className="mt-4 text-2xl font-black">Welcome back</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to your healthcare operations workspace.</p>
        </div>
        {authenticationConfigured ? (
          <SignIn appearance={{ elements: { rootBox: "w-full", card: "w-full rounded-2xl border border-slate-200 shadow-xl", headerTitle: "hidden", headerSubtitle: "hidden" } }} />
        ) : (
          <div role="status" className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm leading-6 text-amber-900">
            Authentication is not configured for this deployment. Configure production Clerk live keys before enabling sign-in.
          </div>
        )}
      </div>
    </main>
  );
}
