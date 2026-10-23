// Next16's exporter uses POSIX-only slash replacement for RSC segment filenames.
// On Windows, collected backslashes can create nested files instead of flat URLs.
// Keep generated files and add equivalent flat aliases for ordinary static hosts.
import fs from "node:fs";
import path from "node:path";

const root = path.resolve("dist");
function flatten(directory, route, prefix = "") {
  for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
    if (item.isSymbolicLink()) throw new Error("Unexpected symlink in static export");
    const name = prefix ? `${prefix}.${item.name}` : item.name;
    const source = path.join(directory, item.name);
    if (item.isDirectory()) flatten(source, route, name);
    else fs.copyFileSync(source, path.join(route, name));
  }
}
function visit(directory) {
  for (const item of fs.readdirSync(directory, { withFileTypes: true })) {
    if (item.isSymbolicLink()) throw new Error("Unexpected symlink in static export");
    if (!item.isDirectory() || item.name === "_next") continue;
    const child = path.join(directory, item.name);
    if (item.name.startsWith("__next.")) flatten(child, directory, item.name);
    else visit(child);
  }
}
if (fs.existsSync(root)) visit(root);
