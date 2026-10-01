import { expect, test } from "@playwright/test";

test("public solution route renders without authenticated state", async ({ page }) => {
  await page.goto("/solutions/operations");
  await expect(page).toHaveTitle(/HEZQARA/i);
  await expect(page.getByRole("heading").first()).toBeVisible();
});
