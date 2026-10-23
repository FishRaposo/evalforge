import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testIgnore: /live.*\.spec\.ts/,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://127.0.0.1:3002",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: process.env.EVALFORGE_USE_STATIC_BUILD === "true" ? "node e2e/serve-static.mjs" : "npm run build && node e2e/serve-static.mjs",
    env: { ...process.env, NEXT_PUBLIC_DEMO_MODE: "true", NEXT_PUBLIC_API_URL: "http://127.0.0.1:9" },
    url: "http://127.0.0.1:3002",
    reuseExistingServer: false,
    timeout: 240000,
  },
});
