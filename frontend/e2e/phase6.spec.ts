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
    expect(await response.json()).toEqual({ status: "ok", service: "hezqara-frontend", scope: "liveness" });
  });

  test("API readiness fails clearly when deployment configuration is absent", async ({ request }) => {
    const response = await request.get("/api/health");
    expect(response.status()).toBe(503);
    expect(await response.json()).toEqual({
      status: "not_ready",
      service: "hezqara-frontend",
      checks: { authenticationConfigured: false, apiOriginConfigured: false, apiReachable: false },
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


test.describe("mobile marketing navigation", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
  });

  test("mobile menu exposes all primary links with correct disclosure state", async ({ page }) => {
    const trigger = page.getByRole("button", { name: "Open navigation menu" });
    const mobileNav = page.getByRole("navigation", { name: "Mobile primary navigation" });

    await expect(trigger).toBeVisible();
    await expect(trigger).toHaveAttribute("aria-expanded", "false");
    await expect(mobileNav).toBeHidden();

    await trigger.click();
    await expect(page.getByRole("button", { name: "Close navigation menu" })).toHaveAttribute("aria-expanded", "true");
    await expect(mobileNav).toBeVisible();

    for (const label of ["Product", "AI workforce", "Solutions", "How it works", "Security"]) {
      await expect(mobileNav.getByRole("link", { name: label })).toBeVisible();
    }
    await expect(mobileNav.getByRole("link", { name: "Sign in" })).toBeVisible();
    await expect(mobileNav.getByRole("link", { name: "Get started" })).toBeVisible();

  });

  test("Escape closes the menu and restores focus to its trigger", async ({ page }) => {
    await page.getByRole("button", { name: "Open navigation menu" }).click();
    await expect(page.getByRole("navigation", { name: "Mobile primary navigation" })).toBeVisible();

    await page.keyboard.press("Escape");

    const trigger = page.getByRole("button", { name: "Open navigation menu" });
    await expect(page.getByRole("navigation", { name: "Mobile primary navigation" })).toBeHidden();
    await expect(trigger).toHaveAttribute("aria-expanded", "false");
    await expect(trigger).toBeFocused();
  });

  test("choosing a mobile navigation link closes the menu", async ({ page }) => {
    const mobileNav = page.getByRole("navigation", { name: "Mobile primary navigation" });
    await page.getByRole("button", { name: "Open navigation menu" }).click();
    await mobileNav.getByRole("link", { name: "Solutions" }).click();

    await expect(page).toHaveURL(/\/solutions$/);
    await expect(page.getByRole("navigation", { name: "Mobile primary navigation" })).toBeHidden();
  });
});

test("desktop primary navigation remains visible without the mobile disclosure button", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("button", { name: /navigation menu/ })).toBeHidden();
});
