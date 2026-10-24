// Serve the actual exported preview; no Next development runtime or dependencies.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve("dist");
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon" };
http.createServer((request, response) => {
  if (!["GET", "HEAD"].includes(request.method)) { response.writeHead(405).end(); return; }
  let target;
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://127.0.0.1").pathname);
    target = path.resolve(root, `.${pathname}`);
    if (target !== root && !target.startsWith(`${root}${path.sep}`)) throw new Error("Outside export");
    const choices = [target, `${target}.html`, path.join(target, "index.html")];
    target = choices.find(candidate => fs.existsSync(candidate) && fs.statSync(candidate).isFile());
  } catch { response.writeHead(400).end(); return; }
  if (!target) { console.error(`Static preview missing ${request.url}`); response.writeHead(404).end("Static preview route not found"); return; }
  response.writeHead(200, { "Content-Type": `${mime[path.extname(target)] || "text/plain"}; charset=utf-8`, "Cache-Control": "no-store" });
  if (request.method === "HEAD") response.end(); else fs.createReadStream(target).pipe(response);
}).listen(3002, "127.0.0.1", () => process.stdout.write("Static preview http://127.0.0.1:3002\n"));
