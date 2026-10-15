export const dynamic = "force-dynamic";

export async function GET(): Promise<Response> {
  const authenticationConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const apiOrigin = process.env.HEZQARA_API_INTERNAL_URL?.replace(/\/+$/, "");

  let apiReachable = false;
  if (apiOrigin) {
    try {
      const response = await fetch(`${apiOrigin}/ready`, {
        cache: "no-store",
        signal: AbortSignal.timeout(2_500),
      });
      apiReachable = response.ok;
    } catch {
      apiReachable = false;
    }
  }

  const ready = authenticationConfigured && apiReachable;

  return Response.json(
    {
      status: ready ? "ready" : "not_ready",
      service: "hezqara-frontend",
      checks: {
        authenticationConfigured,
        apiOriginConfigured: Boolean(apiOrigin),
        apiReachable,
      },
    },
    {
      status: ready ? 200 : 503,
      headers: { "Cache-Control": "no-store" },
    },
  );
}
