import test from "node:test";
import assert from "node:assert/strict";
import { checkRows, horizon } from "./check-future-dates.mjs";

const today = new Date(Date.UTC(2026, 8, 28));

test("horizon is 24 months out", () => {
  assert.equal(horizon(today), "2028-09-28");
});

test("flags placeholder-far dates as errors and near-future non-announcements as warnings", () => {
  const rows = [
    { id: "a", releaseDate: "2031-05-01", source: "curated-bbts-wave5" },
    { id: "b", releaseDate: "2027-03-01", source: "curated-bbts-wave5" },
    { id: "c", releaseDate: "2027-01-01", source: "toyark-densify" },
    { id: "d", releaseDate: "2023-01-01", source: "curated" },
  ];
  const { errors, warnings } = checkRows(rows, { today });
  assert.deepEqual(errors.map((e) => e.split(":")[0]), ["a"]);
  assert.deepEqual(warnings.map((w) => w.split(":")[0]), ["b"]);
});

test("allowlist suppresses", () => {
  const { errors } = checkRows([{ id: "a", releaseDate: "2031-05-01" }], { today, allow: new Set(["a"]) });
  assert.equal(errors.length, 0);
});
