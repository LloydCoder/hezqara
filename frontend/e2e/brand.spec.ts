import { expect, test } from "@playwright/test";

const marketingRoutes = [
  "/", "/product", "/workforce", "/solutions", "/how-it-works",
  "/security", "/compliance", "/enterprise", "/contact", "/pricing",
];

test.describe("official HEZQARA brand identity", () => {
  test("uses the approved logo in the public header and footer across marketing routes", async ({ page }) => {
    for (const route of marketingRoutes) {
      await page.goto(route);
      const headerLogo = page.locator("header a[aria-label='HEZQARA home'] img");
      await expect(headerLogo, `header logo on ${route}`).toBeVisible();
      await expect(headerLogo).toHaveAttribute("src", "/brand/hezqara-logo-horizontal-full-color.svg");
      await expect(page.locator("header picture source")).toHaveAttribute("srcset", "/brand/hezqara-logo-horizontal-tagline-full-color.svg");
      const footer = page.locator("footer");
      await expect(footer.locator("img[alt='HEZQARA']")).toBeVisible();
      await expect(footer).toContainText("A governed AI workforce for healthcare front-office operations.");
    }
  });

  test("uses the approved reversed compact logo on authentication screens", async ({ page }) => {
    for (const route of ["/sign-in", "/sign-up"]) {
      await page.goto(route);
      const logo = page.locator("main a[aria-label='HEZQARA home'] img");
      await expect(logo, `authentication logo on ${route}`).toBeVisible();
      await expect(logo).toHaveAttribute("src", "/brand/hezqara-logo-horizontal-reversed.svg");
    }
  });

  test("publishes the official palette and Inter-first font stack", async ({ page }) => {
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
    expect(tokens).toMatchObject({ navy: "#0f2a47", teal: "#14b8a6", tealDeep: "#0f766e", midnight: "#0b1220" });
    expect(tokens.font).toContain("Inter");
  });

  test("publishes valid favicon, Apple, Android and Open Graph assets", async ({ page, request }) => {
    await page.goto("/");
    await expect(page.locator("link[rel='icon'][type='image/svg+xml']")).toHaveAttribute("href", "/favicon.svg");
    await expect(page.locator("link[rel='apple-touch-icon']")).toHaveAttribute("href", "/apple-icon.png");
    await expect(page.locator("link[rel='manifest']")).toHaveAttribute("href", "/site.webmanifest");
    await expect(page.locator("meta[name='theme-color']")).toHaveAttribute("content", "#0F2A47");
    await expect(page.locator("meta[property='og:image']")).toHaveAttribute("content", /\/opengraph-image/);
    await expect(page.locator("meta[name='twitter:image']")).toHaveAttribute("content", /\/opengraph-image/);

    for (const path of ["/favicon.svg", "/safari-pinned-tab.svg", "/apple-icon.png", "/icon.png"]) {
      const response = await request.get(path);
      expect(response.status(), path).toBe(200);
    }

    const manifest = await request.get("/site.webmanifest");
    expect(manifest.status()).toBe(200);
    const manifestBody = await manifest.json();
    expect(manifestBody.name).toBe("HEZQARA");
    expect(manifestBody.icons).toEqual(expect.arrayContaining([
      expect.objectContaining({ src: "/icon.png", sizes: "512x512", purpose: "any" }),
      expect.objectContaining({ src: "/favicon.svg", sizes: "any", purpose: "any" }),
    ]));
    for (const icon of manifestBody.icons) {
      const response = await request.get(icon.src);
      expect(response.status(), icon.src).toBe(200);
    }

    const socialImage = await request.get("/opengraph-image");
    expect(socialImage.status()).toBe(200);
    expect(socialImage.headers()["content-type"]).toContain("image/png");
  });
});
