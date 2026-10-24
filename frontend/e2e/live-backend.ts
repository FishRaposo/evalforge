import { spawn, spawnSync, execFileSync, type ChildProcess } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

/** Owns disposable data and one real CLI-started API. Never reuses an owner DB. */
export class LiveBackend {
  readonly root = path.resolve(process.cwd(), "..");
  readonly python = process.env.EVALFORGE_TEST_PYTHON ?? path.join(this.root, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
  readonly port = process.env.EVALFORGE_LIVE_API_PORT ?? "8200";
  readonly url = `http://127.0.0.1:${this.port}`;
  readonly directory: string;
  readonly database: string;
  private child: ChildProcess | null = null;
  constructor() {
    fs.mkdirSync(path.join(this.root, ".tmp"), { recursive: true });
    this.directory = fs.mkdtempSync(path.join(this.root, ".tmp", "live-e2e-"));
    this.database = path.join(this.directory, "history.db");
    // Real legacy store before new API startup; future tables must be additive.
    execFileSync(this.python, ["-c", "import sys; from evalforge.storage.history import HistoryStore; s=HistoryStore(sys.argv[1]); s.save_run({'suite_name':'Legacy synthetic run','summary':{'total':1,'passed':1,'failed':0,'pass_rate':1,'avg_score':1},'results':[]})", this.database], { cwd: this.root, windowsHide: true });
  }
  environment(): NodeJS.ProcessEnv {
    return { ...process.env, PYTHONUTF8: "1", EVALFORGE_LLM_MODE: "sim", EVALFORGE_OPENAI_API_KEY: "", OPENAI_API_KEY: "", ANTHROPIC_API_KEY: "",
      EVALFORGE_UPLOAD_DIR: path.join(this.directory, "uploads"),
      EVALFORGE_ALLOWED_ORIGINS: `http://localhost:${process.env.EVALFORGE_LIVE_FRONTEND_PORT ?? "3303"}` };
  }
  async start(): Promise<void> {
    if (this.child) throw new Error("Owned API already running");
    try { await fetch(`${this.url}/api/health`, { signal: AbortSignal.timeout(500) }); throw new Error(`Port ${this.port} occupied; refusing another API`); }
    catch (error) { if (error instanceof Error && error.message.includes("occupied")) throw error; }
    const child = spawn(this.python, ["-m", "evalforge.cli", "serve", "--host", "127.0.0.1", "--port", this.port, "--db", this.database], { cwd: this.root, env: this.environment(), windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    this.child = child;
    let log = "";
    for (const stream of [child.stdout, child.stderr]) stream?.on("data", chunk => { log = (log + chunk.toString()).slice(-12000); fs.appendFileSync(path.join(this.directory, "api.log"), chunk.toString()); });
    const deadline = Date.now() + 45000;
    while (Date.now() < deadline) {
      if (child.exitCode !== null) throw new Error(`API exited ${child.exitCode}: ${log}`);
      if (log.includes("Application startup complete")) {
        try { const response = await fetch(`${this.url}/api/health`); if (response.ok) return; } catch { /* bounded readiness poll */ }
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    await this.stop(); throw new Error(`API timeout: ${log}`);
  }
  async stop(): Promise<void> {
    const child = this.child; this.child = null;
    if (!child || child.exitCode !== null) return;
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Owned API did not stop")), 5000);
      child.once("exit", () => { clearTimeout(timer); resolve(); }); child.kill();
    });
  }
  async restart(): Promise<void> { await this.stop(); await this.start(); }
  profileFiles(id: string): { suite_path: string; response_path: string } {
    return JSON.parse(execFileSync(this.python, ["-c", "import json,sys; from evalforge.portfolio import get_portfolio_profiles; p=next(p for p in get_portfolio_profiles() if p['id']==sys.argv[1]); print(json.dumps({'suite_path':str(p['suite_path']),'response_path':str(p['response_path'])}))", id], { cwd: this.root, encoding: "utf8", windowsHide: true }));
  }
  cli(id: string) {
    const files = this.profileFiles(id);
    const output = path.join(this.directory, `cli-${id}`);
    const result = spawnSync(this.python, ["-m", "evalforge.cli", "eval", files.suite_path, "--backend", "saved", "--response-file", files.response_path, "--strict-evidence", "--db", this.database, "--format", "json", "--output", output, "--evidence-dir", `${output}-evidence`], { cwd: this.root, env: this.environment(), encoding: "utf8", windowsHide: true });
    fs.writeFileSync(`${output}.log`, result.stdout + result.stderr);
    return result;
  }
  sql(statement: string, parameters: unknown[] = []): unknown[][] {
    return JSON.parse(execFileSync(this.python, ["-c", "import json,sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute(sys.argv[2],json.loads(sys.argv[3])).fetchall(); c.commit(); print(json.dumps(r)); c.close()", this.database, statement, JSON.stringify(parameters)], { cwd: this.root, encoding: "utf8", windowsHide: true }));
  }
}
