import { test, expect } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";

const routes = [
  ["overview", "/"],
  ["comparison", "/compare"],
  ["launcher", "/evaluate"],
  ["baseline run", "/runs/demo-1"],
  ["failing run", "/runs/demo-7"],
  ["repaired run", "/runs/demo-repaired"],
  ["error run", "/runs/demo-error"],
] as const;

for (const [name, path] of routes) {
  test(`axe wcag2a/aa: ${name}`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(path);
    await expect(page.locator("main#main")).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}

for (const [name, path] of routes.slice(0, 2)) {
  test(`axe wcag2a/aa at 390px: ${name}`, async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(path);
    await expect(page.locator("main#main")).toBeVisible();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });
}
