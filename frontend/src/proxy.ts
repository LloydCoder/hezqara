import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { isClerkConfigured } from "@/lib/clerk-config";

const isPublicRoute = createRouteMatcher([
  "/",
  "/product(.*)",
  "/solutions(.*)",
  "/workforce(.*)",
  "/pricing(.*)",
  "/how-it-works(.*)",
  "/security(.*)",
  "/enterprise(.*)",
  "/contact(.*)",
  "/compliance(.*)",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/health",
  "/robots.txt",
  "/sitemap.xml",
  "/api/health",
  "/api/v1/health",
  "/api/v1/ready",
]);

const clerkConfigured = isClerkConfigured();

export default clerkConfigured
  ? clerkMiddleware(async (auth, request) => {
      if (!isPublicRoute(request)) {
        await auth.protect();
      }
    })
  : function unconfiguredAuthProxy(request: NextRequest) {
      if (isPublicRoute(request)) {
        return NextResponse.next();
      }
      return new NextResponse("Authentication is not configured for this deployment.", {
        status: 503,
        headers: { "Cache-Control": "no-store" },
      });
    };

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
