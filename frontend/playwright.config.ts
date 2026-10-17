import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: 2,
  use: {
    baseURL: "http://127.0.0.1:3004",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3004",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    // Exercise the production fail-closed contract with deliberately non-live
    // test credentials. These values are fixtures, never real credentials.
    env: {
      ...process.env,
      VERCEL_ENV: "production",
      NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: "pk_test_ZXhhbXBsZS5hY2NvdW50cy5kZXYk",
      CLERK_SECRET_KEY: "sk_test_e2e-only",
    },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
