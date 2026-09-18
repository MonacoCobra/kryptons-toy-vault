import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../..");
const PUBLIC_PATH = join(ROOT, "public/.well-known/assetlinks.json");
const SHA256_RE = /^[0-9A-F]{2}(?::[0-9A-F]{2}){31}$/;
const PACKAGE = "me.kryptontoyvault.app";

describe("Digital Asset Links", () => {
  it("public JSON is a statement list for me.kryptontoyvault.app", () => {
    const data = JSON.parse(readFileSync(PUBLIC_PATH, "utf8"));
    assert.ok(Array.isArray(data) && data.length >= 1, "must be a JSON array");
    const row = data[0];
    assert.ok(
      Array.isArray(row.relation) &&
        row.relation.includes("delegate_permission/common.handle_all_urls"),
    );
    assert.equal(row.target.namespace, "android_app");
    assert.equal(row.target.package_name, PACKAGE);
    const fps = row.target.sha256_cert_fingerprints;
    assert.ok(Array.isArray(fps) && fps.length >= 1);
    const valid = fps.filter((fp) => SHA256_RE.test(fp));
    assert.equal(
      valid.length,
      fps.length,
      "every fingerprint must be colon-separated uppercase SHA-256 (no REPLACE_WITH placeholders on Live)",
    );
  });
});
