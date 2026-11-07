import { expect, test } from "@playwright/test";

test.describe("official HEZQARA brand identity", () => {
  test("uses the approved horizontal logo in the public header", async ({ page }) => {
    await page.goto("/");
    const headerLogo = page.locator("header a[aria-label='HEZQARA home'] img");
    await expect(headerLogo).toBeVisible();
    await expect(headerLogo).toHaveAttribute("src", "/brand/hezqara-logo-horizontal-full-color.svg");
    const desktopLogo = page.locator("header picture source");
    await expect(desktopLogo).toHaveAttribute("srcset", "/brand/hezqara-logo-horizontal-tagline-full-color.svg");
  });

  test("uses the approved logo and official descriptor in the footer", async ({ page }) => {
    await page.goto("/");
    const footer = page.locator("footer");
    await expect(footer.locator("img[alt='HEZQARA']")).toBeVisible();
    await expect(footer).toContainText("A governed AI workforce for healthcare front-office operations.");
  });

  test("publishes the brand palette and Inter font tokens", async ({ page }) => {
    await page.goto("/");
    const tokens = await page.evaluate(() => {
      const root = getComputedStyle(document.documentElement);
      const body = getComputedStyle(document.body);
      return {
        navy: root.getPropertyValue("--hz-navy").trim(),
        teal: root.getPropertyValue("--hz-teal").trim(),
        tealDeep: root.getPropertyValue("--hz-teal-deep").trim(),
        midnight: root.getPropertyValue("--hz-midnight").trim(),
        font: body.fontFamily,
      };
    });
    expect(tokens).toMatchObject({
      navy: "#0f2a47",
      teal: "#14b8a6",
      tealDeep: "#0f766e",
      midnight: "#0b1220",
    });
    expect(tokens.font).toContain("Inter");
  });

  test("exposes working favicon and web manifest assets", async ({ page, request }) => {
    await page.goto("/");
    await expect(page.locator("link[rel='icon'][type='image/svg+xml']")).toHaveAttribute("href", "/favicon.svg");
    await expect(page.locator("link[rel='manifest']")).toHaveAttribute("href", "/site.webmanifest");
    await expect(page.locator("meta[name='theme-color']")).toHaveAttribute("content", "#0F2A47");

    const favicon = await request.get("/favicon.svg");
    expect(favicon.status()).toBe(200);
    expect(favicon.headers()["content-type"]).toContain("image/svg+xml");

    const manifest = await request.get("/site.webmanifest");
    expect(manifest.status()).toBe(200);
    const manifestBody = await manifest.json();
    expect(manifestBody.name).toBe("HEZQARA");
    for (const icon of manifestBody.icons) {
      const response = await request.get(icon.src);
      expect(response.status()).toBe(200);
    }
  });
});
