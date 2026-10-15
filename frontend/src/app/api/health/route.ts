export const dynamic = "force-dynamic";

export function GET(): Response {
  const authConfigured = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);
  const apiConfigured = Boolean(process.env.HEZQARA_API_INTERNAL_URL);

  const ready = authConfigured && apiConfigured;

  return Response.json(
    {
      status: ready ? "ready" : "not_ready",
      service: "hezqara-frontend",
      checks: {
        authenticationConfigured: authConfigured,
        apiOriginConfigured: apiConfigured,
      },
    },
    {
      status: ready ? 200 : 503,
      headers: { "Cache-Control": "no-store" },
    },
  );
}
