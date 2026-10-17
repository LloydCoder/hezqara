/**
 * Treat Clerk test credentials as unconfigured in Vercel production.
 *
 * A present pk_test_ key is not a valid production authentication setup. This
 * guard keeps the public health contract honest and prevents protected routes
 * from treating a development Clerk instance as production auth.
 */
export function isClerkConfigured(): boolean {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  if (!publishableKey) {
    return false;
  }

  if (process.env.VERCEL_ENV !== "production") {
    return true;
  }

  return (
    publishableKey.startsWith("pk_live_") &&
    Boolean(process.env.CLERK_SECRET_KEY?.startsWith("sk_live_"))
  );
}
