import type { NextConfig } from "next";

const backendOrigin = process.env.HEZQARA_API_INTERNAL_URL ?? "http://localhost:8004";
const nextConfig: NextConfig = {
  reactStrictMode:true,
  output:"standalone",
  typedRoutes:true,
  poweredByHeader:false,
  async rewrites(){return [{source:"/api/v1/:path*",destination:`${backendOrigin}/api/v1/:path*`},{source:"/health",destination:`${backendOrigin}/health`}];},
};
export default nextConfig;
