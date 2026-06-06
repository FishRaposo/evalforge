import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("homepage loads with stats cards", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=EvalForge Dashboard")).toBeVisible();
    await expect(page.locator("text=Eval Runs")).toBeVisible();
    await expect(page.locator("text=Pass Rate")).toBeVisible();
    await expect(page.locator("text=Avg Score")).toBeVisible();
    await expect(page.locator("text=Latest Compliance")).toBeVisible();
  });

  test("runs table renders", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=Recent Evaluation Runs")).toBeVisible();
  });

  test("compare page", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.locator("text=Compare Runs")).toBeVisible();
    await expect(page.locator("text=Run A ID")).toBeVisible();
    await expect(page.locator("text=Run B ID")).toBeVisible();
  });

  test("navigation links work", async ({ page }) => {
    await page.goto("/");
    await page.click("text=Compare");
    await expect(page).toHaveURL("/compare");
  });
});
