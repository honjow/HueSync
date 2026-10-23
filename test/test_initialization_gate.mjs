#!/usr/bin/env node
// Node ESM regression test for the asynchronous initialization gate in the
// plugin's Content component. Extracts the real Content declaration from
// src/index.tsx with the project's installed typescript package and executes
// it against a minimal React hook runtime.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");

const sourcePath = fileURLToPath(new URL("../src/index.tsx", import.meta.url));
const source = readFileSync(sourcePath, "utf8");
const sourceFile = ts.createSourceFile(
  sourcePath,
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
);

let contentText = null;
for (const statement of sourceFile.statements) {
  if (!ts.isVariableStatement(statement)) continue;
  for (const declaration of statement.declarationList.declarations) {
    if (ts.isIdentifier(declaration.name) && declaration.name.text === "Content") {
      contentText = source.slice(statement.getStart(sourceFile), statement.getEnd());
      break;
    }
  }
  if (contentText) break;
}
assert.ok(contentText, "expected a Content const declaration in src/index.tsx");

const compiled = ts.transpileModule(contentText.replace(/^export\s+/, ""), {
  compilerOptions: {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.None,
    jsx: ts.JsxEmit.React,
    useDefineForClassFields: false,
  },
}).outputText;

const Fragment = Symbol("Fragment");

function createElement(type, props, ...children) {
  return { type, props: props ?? {}, children: children.flat() };
}

function createRuntime() {
  const slots = [];
  let cursor = 0;
  let effects = [];
  let stateUpdates = 0;

  return {
    reset() {
      cursor = 0;
      effects = [];
    },
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) {
        slots[index] = typeof initial === "function" ? initial() : initial;
      }
      const setState = (next) => {
        stateUpdates += 1;
        slots[index] = typeof next === "function" ? next(slots[index]) : next;
      };
      return [slots[index], setState];
    },
    useEffect(effect) {
      effects.push(effect);
    },
    takeEffects() {
      const queued = effects;
      effects = [];
      return queued;
    },
    stateUpdates() {
      return stateUpdates;
    },
  };
}

function createSandbox(runtime) {
  const useState = (initial) => runtime.useState(initial);
  const useEffect = (effect) => runtime.useEffect(effect);
  const React = { createElement, Fragment, useState, useEffect };

  return {
    React,
    useState,
    useEffect,
    PanelSection: function PanelSection() {},
    PerAppControl: function PerAppControl() {},
    AcStateControl: function AcStateControl() {},
    SuspendModeComponent: function SuspendModeComponent() {},
    PowerLedControl: function PowerLedControl() {},
    RGBComponent: function RGBComponent() {},
    MoreComponent: function MoreComponent() {},
    localizationManager: { getString: () => "Settings" },
    localizeStrEnum: { TITEL_SETTINGS: "TITEL_SETTINGS" },
    console: { log() {}, error() {} },
  };
}

function loadContent() {
  const runtime = createRuntime();
  const Content = vm.runInNewContext(`${compiled}\n;Content;`, createSandbox(runtime), {
    filename: "index-content.js",
  });
  assert.equal(typeof Content, "function", "Content declaration must evaluate to a component");
  return { Content, runtime };
}

function renderContent(Content, runtime, props) {
  runtime.reset();
  const element = Content(props);
  return { element, effects: runtime.takeEffects() };
}

function runEffects(effects) {
  const cleanups = [];
  for (const effect of effects) {
    const cleanup = effect();
    if (typeof cleanup === "function") cleanups.push(cleanup);
  }
  return () => {
    for (const cleanup of cleanups) cleanup();
  };
}

function collectTypeNames(node, names = []) {
  if (node === null || node === undefined) return names;
  if (Array.isArray(node)) {
    for (const child of node) collectTypeNames(child, names);
    return names;
  }
  if (typeof node !== "object") return names;
  if (node.type !== undefined) {
    const type = node.type;
    names.push(
      typeof type === "string"
        ? type
        : type.displayName || type.name || "anonymous",
    );
  }
  collectTypeNames(node.children, names);
  return names;
}

function deferred() {
  let resolve;
  const promise = new Promise((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

async function flushPromises() {
  await new Promise((resolve) => setImmediate(resolve));
}

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

test("Content renders null until asynchronous initialization resolves", async () => {
  const { Content, runtime } = loadContent();
  const initialization = deferred();

  const before = renderContent(Content, runtime, { initialization: initialization.promise });
  assert.equal(before.element, null, "Content must render null before initialization resolves");
  runEffects(before.effects);

  initialization.resolve();
  await flushPromises();

  const after = renderContent(Content, runtime, { initialization: initialization.promise });
  assert.notEqual(after.element, null, "Content must render after initialization resolves");

  const names = collectTypeNames(after.element);
  for (const expected of ["PanelSection", "PerAppControl", "RGBComponent", "MoreComponent"]) {
    assert.ok(
      names.includes(expected),
      `expected ${expected} after initialization, got: ${names.join(", ")}`,
    );
  }
});

test("unmount cleanup suppresses late initialization state updates", async () => {
  const { Content, runtime } = loadContent();
  const initialization = deferred();

  const before = renderContent(Content, runtime, { initialization: initialization.promise });
  assert.equal(before.element, null, "Content must render null before initialization resolves");

  const unmount = runEffects(before.effects);
  unmount();

  initialization.resolve();
  await flushPromises();

  assert.equal(
    runtime.stateUpdates(),
    0,
    "a dismounted Content must not set state after initialization resolves",
  );
});

let failures = 0;
for (const { name, fn } of tests) {
  try {
    await fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    failures += 1;
    console.error(`not ok - ${name}`);
    console.error(`  ${error.message}`);
  }
}

if (failures > 0) {
  console.error(`${failures} of ${tests.length} test(s) failed`);
  process.exit(1);
}
console.log(`${tests.length} test(s) passed`);
