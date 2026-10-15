export const dynamic = "force-dynamic";

export function GET(): Response {
  return Response.json(
    { status: "ok", service: "hezqara-frontend", scope: "liveness" },
    { headers: { "Cache-Control": "no-store" } },
  );
}
