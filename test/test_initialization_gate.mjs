#!/usr/bin/env node
// Execute the real TSX/TypeScript declarations with mocked Decky/React APIs.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import test from "node:test";

const require = createRequire(import.meta.url);
const ts = require("typescript");
const read = (path) => readFileSync(new URL("../" + path, import.meta.url), "utf8");
const compile = (source) => ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.CommonJS,
    jsx: ts.JsxEmit.React,
    useDefineForClassFields: false,
  },
}).outputText;
const source = read("src/index.tsx");
const contentSource = source.slice(source.indexOf("const Content:"), source.indexOf("export default definePlugin"));
const quiet = { log() {}, info() {}, error() {} };
const flush = () => new Promise((resolve) => setImmediate(resolve));
function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
const createElement = (type, props, ...children) => ({ type, props: props || {}, children: children.flat() });
const React = { createElement, Fragment: "Fragment" };
const ui = Object.fromEntries(["PanelSection", "PanelSectionRow", "ButtonItem", "PerAppControl",
  "AcStateControl", "SuspendModeComponent", "PowerLedControl", "RGBComponent", "MoreComponent",
  "FaLightbulb"].map((name) => [name, name]));
const localizationManager = {
  init: async () => {},
  getString: (key, options) => options?.defaultValue || key,
};
const localizeStrEnum = new Proxy({}, { get: (_, key) => key });
function nodes(node) {
  if (!node || typeof node !== "object") return [];
  return [node, ...(node.children || []).flatMap(nodes)];
}
function contentHarness() {
  const slots = [];
  let cursor = 0, updates = 0, queued = [];
  const hooks = {
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = initial;
      return [slots[index], (next) => {
        updates++;
        slots[index] = typeof next === "function" ? next(slots[index]) : next;
      }];
    },
    useEffect(effect, deps) {
      const index = cursor++;
      const old = slots[index];
      if (!old || deps.some((value, i) => value !== old.deps[i])) {
        queued.push(() => {
          old?.cleanup?.();
          slots[index] = { deps, cleanup: effect() };
        });
      }
    },
  };
  const Content = vm.runInNewContext(compile(contentSource) + "\n;Content;", {
    React, ...hooks, ...ui, localizationManager, localizeStrEnum, console: quiet,
  });
  return {
    render(initialize) {
      cursor = 0;
      const element = Content({ initialize });
      const effects = queued;
      queued = [];
      effects.forEach((effect) => effect());
      return element;
    },
    unmount() { slots.forEach((slot) => slot?.cleanup?.()); },
    updates: () => updates,
  };
}
test("shows loading and withholds controls until essential initialization succeeds", async () => {
  const h = contentHarness(), init = deferred(), initialize = () => init.promise;
  const loading = nodes(h.render(initialize));
  assert.ok(loading.some((node) => node.props.role === "status"));
  assert.ok(!loading.some((node) => node.type === "RGBComponent"));
  init.resolve();
  await flush();
  const ready = nodes(h.render(initialize));
  for (const type of ["PerAppControl", "AcStateControl", "PowerLedControl", "RGBComponent", "MoreComponent"]) {
    assert.ok(ready.some((node) => node.type === type), type);
  }
});
test("failure shows an actionable retry and retry restores controls", async () => {
  const h = contentHarness(), first = deferred(), second = deferred();
  let calls = 0;
  const initialize = () => (++calls === 1 ? first.promise : second.promise);
  h.render(initialize);
  first.reject(new Error("settings unavailable"));
  await flush();
  const failed = nodes(h.render(initialize));
  assert.ok(failed.some((node) => node.props.role === "alert"));
  assert.ok(!failed.some((node) => node.type === "RGBComponent"));
  failed.find((node) => node.type === "ButtonItem").props.onClick();
  const retrying = nodes(h.render(initialize));
  assert.equal(calls, 2);
  assert.ok(retrying.some((node) => node.props.role === "status"));
  second.resolve();
  await flush();
  assert.ok(nodes(h.render(initialize)).some((node) => node.type === "RGBComponent"));
});
for (const outcome of ["resolve", "reject"]) {
  test("unmount suppresses late " + outcome + " state updates", async () => {
    const h = contentHarness(), init = deferred();
    h.render(() => init.promise);
    h.unmount();
    const before = h.updates();
    init[outcome](new Error("late"));
    await flush();
    assert.equal(h.updates(), before);
  });
}
test("a superseded effect cannot replace the current initialization state", async () => {
  const h = contentHarness(), old = deferred(), current = deferred();
  h.render(() => old.promise);
  const initialize = () => current.promise;
  h.render(initialize);
  current.reject(new Error("current failure"));
  await flush();
  old.resolve();
  await flush();
  assert.ok(nodes(h.render(initialize)).some((node) => node.props.role === "alert"));
});

function pluginHarness({ settingsInit = async () => {}, versionInit = async () => {}, acRegister } = {}) {
  const counts = { settings: 0, apps: 0, ac: 0, appHandlers: 0, acHandlers: 0, apply: 0,
    versions: 0, appsStopped: 0, acStopped: 0, subscriptionsStopped: 0, cancelled: 0 };
  const applySettings = () => { counts.apply++; };
  applySettings.cancel = () => { counts.cancelled++; };
  const Backend = {
    init: () => { counts.versions++; return versionInit(); }, applySettings,
    resume: async () => {}, suspend: async () => {},
  };
  const Setting = { init: () => { counts.settings++; return settingsInit(); }, notifyChange() {} };
  const RunningApps = {
    register: () => { counts.apps++; },
    unregister: () => { counts.appsStopped++; },
    listenActiveChange: () => { counts.appHandlers++; },
  };
  const ACStateManager = {
    register: () => { counts.ac++; acRegister?.(); },
    unregister: () => { counts.acStopped++; },
    onACStateChange: () => { counts.acHandlers++; },
  };
  const subscription = () => ({ unregister: () => { counts.subscriptionsStopped++; } });
  const modules = {
    "@decky/ui": { ...ui, staticClasses: {}, definePlugin: (factory) => factory() },
    react: {}, "react-icons/fa": ui,
    "./i18n": { localizationManager, localizeStrEnum },
    "./components": ui, "./components/more": ui,
    "./util": { Backend, RunningApps, ACStateManager },
    "./hooks": { Setting },
    "./util/steamUtils": { SteamUtils: {
      RegisterForOnResumeFromSuspend: subscription, RegisterForOnSuspendRequest: subscription,
    } },
  };
  const exports = {};
  vm.runInNewContext(compile(source), {
    React, exports, require: (name) => {
      assert.ok(name in modules, "unexpected import " + name);
      return modules[name];
    }, console: quiet, setTimeout, clearTimeout,
  });
  return { plugin: exports.default, counts };
}
test("essential failure is retryable and simultaneous retries share one attempt", async () => {
  const first = deferred(), second = deferred();
  let calls = 0;
  const { plugin, counts } = pluginHarness({
    settingsInit: () => (++calls === 1 ? first.promise : second.promise),
  });
  const initialize = plugin.content.props.initialize;
  const failed = initialize();
  first.reject(new Error("capabilities unavailable"));
  await assert.rejects(failed);
  assert.equal(counts.apps, 0);
  const retry = initialize();
  assert.equal(initialize(), retry);
  second.resolve();
  await retry;
  assert.equal(counts.settings, 2);
  assert.equal(counts.apps, 1);
  assert.equal(counts.ac, 1);
  assert.equal(counts.appHandlers, 1);
  assert.equal(counts.acHandlers, 1);
  assert.equal(initialize(), retry, "reopening a successful panel must not register again");
  plugin.onDismount();
});
test("a pending or failed optional version check never blocks controls", async () => {
  const version = deferred();
  const { plugin, counts } = pluginHarness({ versionInit: () => version.promise });
  await plugin.content.props.initialize();
  assert.equal(counts.apply, 1);
  assert.equal(counts.versions, 1);
  version.reject(new Error("offline"));
  await flush();
  await plugin.content.props.initialize();
  assert.equal(counts.apps, 1);
  plugin.onDismount();
});
test("partial listener registration is rolled back before retry", async () => {
  let calls = 0;
  const { plugin, counts } = pluginHarness({
    acRegister: () => { if (++calls === 1) throw new Error("AC unavailable"); },
  });
  await assert.rejects(plugin.content.props.initialize());
  assert.equal(counts.appsStopped, 1);
  assert.equal(counts.acStopped, 1);
  await plugin.content.props.initialize();
  assert.equal(counts.appHandlers, 1);
  assert.equal(counts.acHandlers, 1);
  plugin.onDismount();
});
test("unload during initialization cannot register listeners or apply settings later", async () => {
  const settings = deferred();
  const { plugin, counts } = pluginHarness({ settingsInit: () => settings.promise });
  const initialization = plugin.content.props.initialize();
  await flush();
  plugin.onDismount();
  settings.resolve();
  await assert.rejects(initialization, /unloaded/);
  assert.equal(counts.apps, 0);
  assert.equal(counts.ac, 0);
  assert.equal(counts.apply, 0);
  assert.equal(counts.versions, 0);
  assert.equal(counts.subscriptionsStopped, 2);
  assert.equal(counts.cancelled, 1);
});

function backendHarness(call) {
  const exports = {};
  const modules = {
    "../hooks": {}, "@decky/api": { call }, lodash: { debounce: (fn) => fn },
    ".": {}, "./const": {}, "./suspendPolicy": {}, "./profilePolicy": {},
    "./versionCache": { getVersionCache: () => null, setVersionCache() {}, getStaleCache: () => null },
  };
  vm.runInNewContext(compile(read("src/util/backend.ts")), {
    exports, require: (name) => {
      assert.ok(name in modules, "unexpected import " + name);
      return modules[name];
    }, console: quiet,
  });
  return exports.Backend;
}
test("Backend shares background version requests and exposes initialized data immediately", async () => {
  const latest = deferred(), calls = [];
  const Backend = backendHarness(async (method) => {
    calls.push(method);
    return method === "get_version" ? "3.9.0" : latest.promise;
  });
  assert.equal(Backend.data.getCurrentVersion(), "");
  const pending = Backend.init();
  assert.equal(Backend.init(), pending);
  await flush();
  assert.deepEqual(calls, ["get_version", "get_latest_version"]);
  latest.resolve("3.9.1");
  await pending;
  assert.equal(Backend.data.getCurrentVersion(), "3.9.0");
  assert.equal(Backend.data.getLatestVersion(), "3.9.1");
});
test("current-version failure does not prevent latest-version lookup", async () => {
  const Backend = backendHarness(async (method) => {
    if (method === "get_version") throw new Error("version unavailable");
    return "3.9.1";
  });
  await Backend.init();
  assert.equal(Backend.data.getCurrentVersion(), "");
  assert.equal(Backend.data.getLatestVersion(), "3.9.1");
});

test("MoreComponent waits on the shared check and ignores completion after unmount", async () => {
  const pending = deferred();
  const effects = [];
  let updates = 0, checks = 0;
  const Backend = {
    data: { getCurrentVersion: () => "", getLatestVersion: () => "" },
    init: () => { checks++; return pending.promise; },
    getLatestVersion: () => { throw new Error("duplicate version request"); },
  };
  const modules = {
    "@decky/ui": ui,
    react: {
      useState: (initial) => [initial, () => { updates++; }],
      useEffect: (effect) => { effects.push(effect); },
    },
    "../i18n": { localizationManager, localizeStrEnum },
    "../util": { Backend },
    "../util/versionCache": { getVersionCache: () => null, getStaleCache: () => null },
    ".": { ActionButtonItem: "ActionButtonItem" },
  };
  const exports = {};
  vm.runInNewContext(compile(read("src/components/more.tsx")), {
    exports, React, console: quiet, require: (name) => modules[name],
  });
  exports.MoreComponent();
  const cleanup = effects[0]();
  assert.equal(checks, 1);
  cleanup();
  const before = updates;
  pending.resolve();
  await flush();
  assert.equal(updates, before);
});
