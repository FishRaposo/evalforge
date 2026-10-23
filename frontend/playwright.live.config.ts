import { defineConfig, devices } from "@playwright/test";
const port = process.env.EVALFORGE_LIVE_FRONTEND_PORT ?? "3303";
const apiPort = process.env.EVALFORGE_LIVE_API_PORT ?? "8200";
export default defineConfig({
  testDir: "./e2e", testMatch: "live-app.spec.ts", workers: 1, retries: 0,
  fullyParallel: false, timeout: 60000,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-live-report" }]],
  use: { baseURL: `http://localhost:${port}`, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.EVALFORGE_API_ONLY === "true" ? undefined : {
    command: `npm run build:connected && npm run start:connected -- --port ${port}`,
    env: { ...process.env, NEXT_PUBLIC_DEMO_MODE: "false", NEXT_PUBLIC_API_URL: `http://127.0.0.1:${apiPort}` },
    url: `http://localhost:${port}`, reuseExistingServer: false, timeout: 240000,
  },
});
