import { expect, test } from "@playwright/test";

test.describe("public application smoke", () => {
  test("marketing home renders without authentication", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/HEZQARA/i);
    await expect(page.getByRole("link", { name: /See HEZQARA in action|Start with HEZQARA/i }).first()).toBeVisible();
  });

  test("workforce marketing surface is publicly reachable", async ({ page }) => {
    await page.goto("/workforce");
    await expect(page).toHaveTitle(/HEZQARA/i);
    await expect(page.getByRole("heading").first()).toBeVisible();
  });

  test("frontend liveness is public and independent of API configuration", async ({ request }) => {
    const response = await request.get("/health");
    expect(response.status()).toBe(200);
    await expect(response).toBeOK();
    await expect(response).toHaveJSON({ status: "ok", service: "hezqara-frontend", scope: "liveness" });
  });

  test("API readiness fails clearly when deployment configuration is absent", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.status()).toBe(503);
    await expect(response).toHaveJSON({
      status: "not_ready",
      service: "hezqara-frontend",
      checks: { authenticationConfigured: false, apiOriginConfigured: false },
    });
  });

  test("robots and sitemap are public and never emit localhost canonical URLs", async ({ request }) => {
    const robots = await request.get("/robots.txt");
    expect(robots.status()).toBe(200);
    expect(await robots.text()).toContain("https://hezqara.vercel.app/sitemap.xml");

    const sitemap = await request.get("/sitemap.xml");
    expect(sitemap.status()).toBe(200);
    const sitemapBody = await sitemap.text();
    expect(sitemapBody).toContain("https://hezqara.vercel.app/");
    expect(sitemapBody).not.toContain("localhost");
  });
});
