import type { NextConfig } from "next";

const backendOrigin =
  process.env.HEZQARA_API_INTERNAL_URL ??
  (process.env.NODE_ENV === "production" ? undefined : "http://localhost:8004");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  typedRoutes: true,
  poweredByHeader: false,
  async rewrites() {
    if (!backendOrigin) {
      return [];
    }

    return [
      {
        source: "/api/v1/health",
        destination: `${backendOrigin}/health`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${backendOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
