import { register } from "node:module";
import { pathToFileURL } from "node:url";
import path from "node:path";
import { readFileSync } from "node:fs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const src = path.join(root, "src");

const hook = `
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const src = ${JSON.stringify(src)};

export async function resolve(specifier, context, nextResolve) {
  const q = specifier.indexOf("?");
  const bare = q === -1 ? specifier : specifier.slice(0, q);
  const query = q === -1 ? "" : specifier.slice(q);
  let resolved;
  if (bare.startsWith("@/")) {
    let target = src + "/" + bare.slice(2);
    if (!/\\.(ts|tsx|js|mjs|json)$/.test(target)) target += ".ts";
    resolved = await nextResolve(pathToFileURL(target).href, context);
  } else {
    resolved = await nextResolve(bare, context);
  }
  if (query) return { ...resolved, url: resolved.url + query };
  return resolved;
}

export async function load(url, context, nextLoad) {
  const q = url.indexOf("?");
  const clean = q === -1 ? url : url.slice(0, q);
  const query = q === -1 ? "" : url.slice(q);
  if (query.split("&").includes("raw") || query.includes("raw")) {
    const source = readFileSync(fileURLToPath(clean), "utf8");
    return {
      format: "module",
      shortCircuit: true,
      source: "export default " + JSON.stringify(source),
    };
  }
  if (clean.endsWith(".json")) {
    const source = readFileSync(fileURLToPath(clean), "utf8");
    return {
      format: "module",
      shortCircuit: true,
      source: "export default " + source,
    };
  }
  return nextLoad(url, context);
}
`;

register("data:text/javascript," + encodeURIComponent(hook), pathToFileURL("./"));
