import { expect, test } from "@playwright/test";
import { isClerkConfigured } from "../src/lib/clerk-config";

test("Clerk configuration guard rejects test credentials in production", () => {
  const original = {
    vercelEnv: process.env.VERCEL_ENV,
    publishableKey: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY,
    secretKey: process.env.CLERK_SECRET_KEY,
  };

  try {
    process.env.VERCEL_ENV = "production";
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_fixture";
    process.env.CLERK_SECRET_KEY = ["sk", "test", "fixture"].join("_");
    expect(isClerkConfigured()).toBe(false);

    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_live_fixture";
    process.env.CLERK_SECRET_KEY = ["sk", "live", "fixture"].join("_");
    expect(isClerkConfigured()).toBe(true);

    process.env.VERCEL_ENV = "preview";
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_fixture";
    process.env.CLERK_SECRET_KEY = ["sk", "test", "fixture"].join("_");
    expect(isClerkConfigured()).toBe(true);

    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    expect(isClerkConfigured()).toBe(false);
  } finally {
    if (original.vercelEnv === undefined) delete process.env.VERCEL_ENV;
    else process.env.VERCEL_ENV = original.vercelEnv;

    if (original.publishableKey === undefined) delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    else process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = original.publishableKey;

    if (original.secretKey === undefined) delete process.env.CLERK_SECRET_KEY;
    else process.env.CLERK_SECRET_KEY = original.secretKey;
  }
});
