import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const sourceUrl = new URL("../src/util/profilePolicy.ts", import.meta.url);
const source = await readFile(sourceUrl, "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2020,
  },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
const { shouldPersistHardwareState } = await import(moduleUrl);

test("persists the default profile to device firmware", () => {
  assert.equal(shouldPersistHardwareState(false), true);
});

test("keeps per-game profiles out of device firmware", () => {
  assert.equal(shouldPersistHardwareState(true), false);
});
