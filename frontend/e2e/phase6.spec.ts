import { expect, test } from "@playwright/test";

test.describe("public application smoke", () => {
  test("marketing home renders without authentication", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/HEZQARA/i);
    await expect(page.getByRole("link", { name: /get started|sign up/i }).first()).toBeVisible();
  });

  test("workforce marketing surface is publicly reachable", async ({ page }) => {
    await page.goto("/workforce");
    await expect(page).toHaveTitle(/HEZQARA/i);
    await expect(page.getByRole("heading").first()).toBeVisible();
  });
});
