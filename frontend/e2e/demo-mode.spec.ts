import { expect, test } from "@playwright/test";

/**
 * Smoke spec for the offline demo-mode fallback. The Playwright webServer runs
 * `npm run dev` with no EvalForge history API behind it, so the dashboard should
 * transparently fall back to deterministic demo data and surface the demo
 * banner. This guarantees the UI is usable with no backend.
 */
test.describe("Demo mode (no backend)", () => {
  test("dashboard shows the demo banner and sample runs", async ({ page }) => {
    await page.goto("/");
    const banner = page.getByTestId("demo-banner");
    await expect(banner).toBeVisible();
    await expect(banner).toContainText("Demo mode");
    // Demo runs render in the table.
    await expect(page.getByText("Recent Evaluation Runs")).toBeVisible();
    await expect(page.getByText("rag_basic").first()).toBeVisible();
  });

  test("metrics cards populate from demo data", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("EVAL RUNS")).toBeVisible();
    // Cumulative pass rate card should show a non-N/A percentage.
    await expect(page.getByText("CUMULATIVE PASS RATE")).toBeVisible();
  });

  test("compare page falls back to a demo comparison", async ({ page }) => {
    await page.goto("/compare");
    await page.fill("#runA", "1");
    await page.fill("#runB", "2");
    await page.getByRole("button", { name: "Compare" }).click();
    await expect(page.getByText("Comparison Results")).toBeVisible();
    await expect(page.getByTestId("demo-banner")).toBeVisible();
  });
});
