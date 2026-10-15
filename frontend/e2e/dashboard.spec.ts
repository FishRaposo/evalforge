import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("homepage loads with stats cards", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=EvalForge Dashboard")).toBeVisible();
    await expect(page.getByText("EVAL RUNS")).toBeVisible();
    await expect(page.getByText("CUMULATIVE PASS RATE")).toBeVisible();
    await expect(page.getByText("AVG SCORE")).toBeVisible();
    await expect(page.getByText("LATEST COMPLIANCE")).toBeVisible();
  });

  test("runs table renders", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=Recent Evaluation Runs")).toBeVisible();
  });

  test("compare page", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.locator("text=Compare Runs")).toBeVisible();
    await expect(page.getByLabel("Baseline run")).toBeVisible();
    await expect(page.getByLabel("Current run")).toBeVisible();
  });

  test("navigation links work", async ({ page }) => {
    await page.goto("/");
    await page.click("text=Compare");
    await expect(page).toHaveURL("/compare");
  });
});
