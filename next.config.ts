/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8004",
    NEXT_PUBLIC_DEMO_CLINIC_ID: process.env.NEXT_PUBLIC_DEMO_CLINIC_ID ?? "demo_clinic",
  },
};

module.exports = nextConfig;
