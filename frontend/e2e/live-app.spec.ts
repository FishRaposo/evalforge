import { test, expect, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";
import fs from "node:fs";
import { LiveBackend } from "./live-backend";

let backend: LiveBackend;
const runIds: Record<string, number> = {};
const terminal = new Set(["completed", "failed", "interrupted"]);

async function api(route: string, init?: RequestInit) {
  // Synchronous CLI subprocesses block Node's idle-socket timers between requests.
  const response = await fetch(`${backend.url}${route}`, { ...init, headers: { Connection: "close", ...init?.headers } });
  return { status: response.status, body: await response.json() };
}
const post = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
async function finished(id: string) {
  let job;
  await expect.poll(async () => {
    job = (await api(`/api/evaluations/${id}`)).body;
    return terminal.has(job.status);
  }).toBe(true);
  return job! as { id: string; status: string; run_id: number; exit_code: number; completed_cases: number };
}

test.describe.configure({ mode: "serial" });
test.beforeAll(async () => {
  backend = new LiveBackend();
  await backend.start();
  for (const [id, exit] of Object.entries({ baseline: 0, candidate: 1, repaired: 0, indeterminate: 2 })) {
    const result = backend.cli(id);
    expect(result.status, result.stdout + result.stderr).toBe(exit);
    const rows = (await api("/api/runs?limit=1")).body;
    runIds[id] = rows[0].id;
  }
});
test.afterAll(async () => { await backend?.stop(); });

test("real public CLI saves exact gate outcomes, evidence and legacy history", async () => {
  const profiles = await api("/api/evaluation-profiles");
  expect(profiles.status).toBe(200);
  expect(profiles.body.profiles.filter((p: { uploaded: boolean }) => !p.uploaded)).toHaveLength(4);
  expect(JSON.stringify(profiles.body)).not.toContain(backend.root);
  for (const [id, exit] of Object.entries({ baseline: 0, candidate: 1, repaired: 0, indeterminate: 2 })) {
    const result = (await api(`/api/runs/${runIds[id]}`)).body;
    expect(result.gate.exit_code).toBe(exit);
    expect(result.gate.quality_validated).toBe(false);
    expect(result.cases).toHaveLength(100);
    expect(result.provenance.origin).toBe(id === "indeterminate" ? "unknown" : "synthetic");
    expect(result.cases[0].authoritative_sources.length).toBeGreaterThan(0);
  }
  const legacy = (await api("/api/runs/1")).body;
  expect(legacy.suite_name).toBe("Legacy synthetic run");
  expect(legacy.provenance.origin).toBe("unknown");
  expect(legacy.gate).toBeNull();
  const comparison = (await api("/api/runs/compare", post({ run_a_id: runIds.baseline, run_b_id: runIds.candidate }))).body;
  expect(comparison.comparable).toBe(true);
  expect(comparison.case_deltas.filter((d: { change: string }) => d.change === "regressed")).toHaveLength(6);
  const incompatible = (await api("/api/runs/compare", post({ run_a_id: 1, run_b_id: runIds.candidate }))).body;
  expect(incompatible.comparable).toBe(false);
});

test("HTTP uploads validate without execution; jobs deduplicate and survive restart", async () => {
  const files = backend.profileFiles("repaired");
  const rowsBefore = backend.sql("SELECT COUNT(*) FROM runs")[0][0];
  const upload = new FormData();
  upload.append("suite", new Blob([fs.readFileSync(files.suite_path)]), "suite.yaml");
  upload.append("responses", new Blob([fs.readFileSync(files.response_path)]), "responses.jsonl");
  const imported = await api("/api/evaluation-profiles", { method: "POST", body: upload });
  expect(imported.status).toBe(201);
  expect(imported.body.uploaded).toBe(true);
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(rowsBefore);
  const request_id = randomUUID();
  const launched = await api("/api/evaluations", post({ profile_id: imported.body.id, request_id }));
  expect(launched.status).toBe(202);
  const job = await finished(launched.body.id);
  expect(job.status).toBe("completed");
  expect(job.exit_code).toBe(0);
  expect(job.completed_cases).toBe(100);
  const repeated = await api("/api/evaluations", post({ profile_id: imported.body.id, request_id }));
  expect(repeated.status).toBe(200);
  expect(repeated.body.id).toBe(job.id);
  expect((await api("/api/evaluations", post({ profile_id: "candidate", request_id }))).status).toBe(409);
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(Number(rowsBefore) + 1);
  const invalid = new FormData();
  invalid.append("suite", new Blob(["name: Unsafe\nincludes: ['../../secret.yaml']\ntest_cases: []"]), "unsafe.yaml");
  invalid.append("responses", new Blob(["{}"]), "bad.jsonl");
  expect((await api("/api/evaluation-profiles", { method: "POST", body: invalid })).status).toBe(400);
  const originBlocked = await api("/api/evaluations", { ...post({ profile_id: "baseline", request_id: randomUUID() }), headers: { "Content-Type": "application/json", Origin: "https://untrusted.invalid" } });
  expect(originBlocked.status).toBe(403);
  await backend.restart();
  expect((await api(`/api/evaluations/${job.id}`)).body.run_id).toBe(job.run_id);
  expect((await api("/api/evaluation-profiles")).body.profiles.some((p: { id: string }) => p.id === imported.body.id)).toBe(true);
  expect((await api(`/api/runs/${job.run_id}`)).body.gate.exit_code).toBe(0);
});

test("startup interrupts a durable unfinished-job fixture without rerunning it", async () => {
  await backend.stop();
  const jobId = randomUUID();
  const requestId = randomUUID();
  const count = backend.sql("SELECT COUNT(*) FROM runs")[0][0];
  // Explicit crash-state fixture, not a claim that arbitrary power loss was tested.
  backend.sql("INSERT INTO evaluation_jobs (id,profile_id,request_id,status,total_cases,created_at,updated_at) VALUES (?,?,?,'running',100,?,?)", [jobId, "baseline", requestId, new Date().toISOString(), new Date().toISOString()]);
  await backend.start();
  const recovered = (await api(`/api/evaluations/${jobId}`)).body;
  expect(recovered.status).toBe("interrupted");
  expect(recovered.run_id).toBeNull();
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(count);
  const repeated = await api("/api/evaluations", post({ profile_id: "baseline", request_id: requestId }));
  expect(repeated.body.id).toBe(jobId);
  expect(repeated.body.status).toBe("interrupted");
  const explicitNew = await api("/api/evaluations", post({ profile_id: "baseline", request_id: randomUUID() }));
  expect(explicitNew.status).toBe(202);
  expect((await finished(explicitNew.body.id)).exit_code).toBe(0);
});

async function connected(page: Page, route = "/") {
  await page.goto(route);
  await page.getByLabel("Data source", { exact: true }).selectOption("connected");
  await expect(page.getByLabel("Data source", { exact: true })).toHaveValue("connected");
}
function healthy(page: Page) {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  return errors;
}

test("browser imports files, explicitly evaluates, inspects real evidence and compares", async ({ page }) => {
  const errors = healthy(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await connected(page, "/evaluate");
  await expect(page.getByRole("heading", { name: "Run an evidence evaluation" })).toBeVisible();
  await expect(page.getByTestId("evaluation-profile").locator("option")).toHaveCount(6); // 4 presets + earlier upload + placeholder
  const files = backend.profileFiles("candidate");
  const count = backend.sql("SELECT COUNT(*) FROM runs")[0][0];
  await page.getByTestId("suite-upload").setInputFiles(files.suite_path);
  await page.getByTestId("responses-upload").setInputFiles(files.response_path);
  const responsePromise = page.waitForResponse(response => response.url().endsWith("/api/evaluation-profiles") && response.request().method() === "POST");
  await page.getByTestId("validate-import").click();
  const importedResponse = await responsePromise;
  expect(importedResponse.status()).toBe(201);
  const profile = await importedResponse.json();
  await expect(page.getByTestId("evaluation-profile")).toHaveValue(profile.id);
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(count);
  await page.getByTestId("run-evaluation").click();
  await expect(page.getByTestId("evaluation-job").getByRole("heading", { name: "Completed", exact: true })).toBeVisible();
  await expect(page.getByTestId("release-gate")).toContainText("Release blocked");
  await expect(page.getByTestId("evaluation-job")).toContainText("100 / 100");
  await page.getByTestId("open-evaluation-report").click();
  await expect(page).toHaveURL(/\/runs\/\d+$/);
  await expect(page.getByRole("heading", { name: "Test cases (100)" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("synthetic evidence contracts");
  await page.getByRole("complementary", { name: "Test cases" }).getByRole("button").nth(1).click();
  await expect(page.getByTestId("case-ef-answerable-002")).toContainText("not an approved claim-to-source support link");
  await expect(page.getByTestId("case-ef-answerable-002")).toContainText("Aster trial policy");
  await page.getByTestId("case-ef-answerable-002").evaluate(element => element.scrollIntoView({ block: "start" }));
  await page.screenshot({ path: `${backend.directory}/connected-evidence-desktop.png`, animations: "disabled" });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Test cases (100)" })).toBeVisible();
  await expect(page.getByLabel("Data source", { exact: true })).toHaveValue("connected");
  await page.getByRole("link", { name: "Compare", exact: true }).click();
  await page.getByLabel("Baseline run").selectOption(String(runIds.baseline));
  await page.getByLabel("Current run").selectOption(String(runIds.candidate));
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Case changes, made visible" })).toBeVisible();
  await expect(page.getByText("-6.0 pp", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Baseline answer & evidence" })).toBeVisible();
  await page.locator(".comparison-cases").evaluate(element => element.scrollIntoView({ block: "start" }));
  await page.screenshot({ path: `${backend.directory}/connected-compare-desktop.png`, animations: "disabled" });
  await page.getByLabel("Baseline run").selectOption("1");
  await page.getByRole("button", { name: "Compare", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Different contracts — comparison limited" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("connected routes remain readable at three viewports and preserve legacy unknowns", async ({ page }) => {
  const errors = healthy(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await connected(page);
  for (const [width, height] of [[390, 844], [768, 1024], [1440, 900]]) {
    await page.setViewportSize({ width, height });
    for (const route of ["/", "/evaluate", "/compare", `/runs/${runIds.candidate}`, "/runs/1"]) {
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      if (route === "/") await expect(page.getByRole("heading", { name: "Recent Evaluation Runs" })).toBeVisible();
      if (route === "/evaluate") await expect(page.getByTestId("evaluation-profile")).toBeEnabled();
      if (route.includes(`/runs/${runIds.candidate}`)) {
        await expect(page.getByRole("heading", { name: "Test cases (100)" })).toBeVisible();
        const cases = page.getByRole("complementary", { name: "Test cases" });
        await expect(cases.getByRole("button").first().locator("span").nth(1)).toBeVisible();
        expect((await cases.boundingBox())!.height).toBeLessThanOrEqual(width < 768 ? 360 : height * 0.65 + 1);
      }
      if (route === "/runs/1") {
        await expect(page.getByTestId("release-gate")).toContainText("Gate unavailable");
        await expect(page.getByText("No case evidence recorded in this legacy report.")).toBeVisible();
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), `Horizontal clipping at ${route} ${width}`).toBe(true);
      await expect(page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "Evaluate", exact: true })).toBeInViewport();
      if (route === "/evaluate" || route.includes(`/runs/${runIds.candidate}`)) {
        await page.screenshot({ path: `${backend.directory}/connected-${route === "/evaluate" ? "launcher" : "run"}-${width}.png`, animations: "disabled" });
      }
    }
  }
  await page.goto("/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main$/);
  await expect(page.locator("main")).toBeFocused();
  expect(errors).toEqual([]);
});

test("browser rejects invalid imports and changed inputs; storage failure never fabricates a report", async ({ page }) => {
  await connected(page, "/evaluate");
  const before = backend.sql("SELECT COUNT(*) FROM runs")[0][0];
  await page.getByTestId("suite-upload").setInputFiles({ name: "unsafe.yaml", mimeType: "text/yaml", buffer: Buffer.from("name: unsafe\nincludes: ['../../private.yaml']\ntest_cases: []") });
  await page.getByTestId("responses-upload").setInputFiles({ name: "responses.jsonl", mimeType: "text/plain", buffer: Buffer.from("{}") });
  await page.getByTestId("validate-import").click();
  await expect(page.getByRole("alert").filter({ hasText: "Evaluation request needs attention" })).toContainText("Invalid saved inputs");
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(before);
  const files = backend.profileFiles("baseline");
  await page.getByTestId("suite-upload").setInputFiles(files.suite_path);
  await page.getByTestId("responses-upload").setInputFiles(files.response_path);
  const responsePromise = page.waitForResponse(response => response.url().endsWith("/api/evaluation-profiles") && response.request().method() === "POST");
  await page.getByTestId("validate-import").click();
  const profile = await (await responsePromise).json();
  await expect(page.getByTestId("evaluation-profile")).toHaveValue(profile.id);
  fs.appendFileSync(`${backend.directory}/uploads/${profile.id}/responses.jsonl`, "\n");
  await page.getByTestId("run-evaluation").click();
  await expect(page.getByRole("alert").filter({ hasText: "Evaluation request needs attention" })).toContainText("Profile inputs are invalid or changed");
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(before);

  // Actual SQLite failure injected solely in this disposable test database.
  backend.sql("CREATE TRIGGER test_report_storage_failure BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT, 'test storage failure'); END");
  try {
    await page.getByTestId("evaluation-profile").selectOption("baseline");
    await page.getByTestId("run-evaluation").click();
    await expect(page.getByTestId("evaluation-job").getByRole("heading", { name: "Failed", exact: true })).toBeVisible();
    await expect(page.getByTestId("open-evaluation-report")).toHaveCount(0);
    expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(before);
  } finally { backend.sql("DROP TRIGGER test_report_storage_failure"); }
  await page.getByTestId("run-evaluation").click();
  await expect(page.getByTestId("evaluation-job").getByRole("heading", { name: "Completed", exact: true })).toBeVisible();
  await expect(page.getByTestId("open-evaluation-report")).toBeVisible();
  expect(backend.sql("SELECT COUNT(*) FROM runs")[0][0]).toBe(Number(before) + 1);
});

test("backend outage stays an error; Retry reconnects and sample switch is explicit", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  await connected(page);
  await expect(page.getByRole("heading", { name: "Recent Evaluation Runs" })).toBeVisible();
  await backend.stop();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Connected API unavailable" })).toBeVisible();
  await expect(page.getByText("Interactive sample data", { exact: true })).toHaveCount(0);
  await backend.start();
  await page.getByRole("button", { name: "Retry connection", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Recent Evaluation Runs" })).toBeVisible();
  await backend.stop();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Connected API unavailable" })).toBeVisible();
  await page.getByRole("button", { name: "Enter sample mode" }).click();
  await expect(page.getByText("Interactive sample data", { exact: true })).toBeVisible();
  const apiCalls: string[] = [];
  page.on("request", request => { if (request.url().includes(":8200")) apiCalls.push(request.url()); });
  await page.getByRole("button", { name: "Start guided demo" }).click();
  await page.getByRole("button", { name: "Introduce wrong source", exact: true }).click();
  await expect(page.getByTestId("release-gate")).toContainText("Release blocked");
  await page.getByRole("button", { name: "Reset demo" }).click();
  await expect(page.getByTestId("release-gate")).toContainText("Contract passed");
  expect(apiCalls).toEqual([]);
  expect(pageErrors).toEqual([]);
  await backend.start();
});
