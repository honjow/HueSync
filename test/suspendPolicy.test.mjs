import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const sourceUrl = new URL("../src/util/suspendPolicy.ts", import.meta.url);
const source = await readFile(sourceUrl, "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2020,
  },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
const { shouldHandleSuspendResume } = await import(moduleUrl);

test("forwards lifecycle events while RGB control is enabled", () => {
  assert.equal(
    shouldHandleSuspendResume({
      rgbControlEnabled: true,
      powerLedSuspendOff: false,
      powerLedSupported: false,
    }),
    true,
  );
});

test("forwards lifecycle events for the independent power LED suspend option", () => {
  assert.equal(
    shouldHandleSuspendResume({
      rgbControlEnabled: false,
      powerLedSuspendOff: true,
      powerLedSupported: true,
    }),
    true,
  );
});

test("does not run unrelated device lifecycle handling for a stale power LED setting", () => {
  assert.equal(
    shouldHandleSuspendResume({
      rgbControlEnabled: false,
      powerLedSuspendOff: true,
      powerLedSupported: false,
    }),
    false,
  );
});

test("skips lifecycle events when neither feature needs them", () => {
  assert.equal(
    shouldHandleSuspendResume({
      rgbControlEnabled: false,
      powerLedSuspendOff: false,
      powerLedSupported: true,
    }),
    false,
  );
});
