import rawStatements from "./assetlinks.json";

/** Colon-separated uppercase SHA-256, Digital Asset Links statement format. */
export const SHA256_FINGERPRINT_RE =
  /^[0-9A-F]{2}(?::[0-9A-F]{2}){31}$/;

export const ANDROID_PACKAGE_NAME = "me.kryptontoyvault.app";

export type AssetLinkStatement = {
  relation: string[];
  target: {
    namespace: string;
    package_name: string;
    sha256_cert_fingerprints: string[];
  };
};

function isStatement(value: unknown): value is AssetLinkStatement {
  if (!value || typeof value !== "object") return false;
  const row = value as AssetLinkStatement;
  return (
    Array.isArray(row.relation) &&
    !!row.target &&
    typeof row.target.package_name === "string" &&
    Array.isArray(row.target.sha256_cert_fingerprints)
  );
}

/** Live statement list with only well-formed fingerprints (placeholders stripped). */
export function publishedAssetLinks(): AssetLinkStatement[] {
  const input = Array.isArray(rawStatements) ? rawStatements : [];
  return input.filter(isStatement).map((row) => ({
    relation: row.relation,
    target: {
      namespace: row.target.namespace || "android_app",
      package_name: row.target.package_name || ANDROID_PACKAGE_NAME,
      sha256_cert_fingerprints: row.target.sha256_cert_fingerprints.filter((fp) =>
        SHA256_FINGERPRINT_RE.test(fp),
      ),
    },
  }));
}

export const ASSETLINKS_JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "public, max-age=0, must-revalidate",
} as const;
