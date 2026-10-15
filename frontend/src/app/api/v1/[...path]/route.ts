export const dynamic = "force-dynamic";

function backendUnavailable(): Response {
  return Response.json(
    {
      error: {
        code: "backend_not_configured",
        message: "The HEZQARA API origin is not configured for this deployment.",
      },
    },
    {
      status: 503,
      headers: { "Cache-Control": "no-store" },
    },
  );
}

export const GET = backendUnavailable;
export const HEAD = backendUnavailable;
export const POST = backendUnavailable;
export const PUT = backendUnavailable;
export const PATCH = backendUnavailable;
export const DELETE = backendUnavailable;
export const OPTIONS = backendUnavailable;
