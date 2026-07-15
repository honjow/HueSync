import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const router = { MainRunningApp: null };
globalThis.__huesyncTestRouter = router;

const sourceUrl = new URL("../src/util/runningApps.ts", import.meta.url);
const source = (await readFile(sourceUrl, "utf8")).replace(
  'import { Router } from "@decky/ui";',
  "const Router = globalThis.__huesyncTestRouter;",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2020,
  },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
const { RunningApps } = await import(moduleUrl);

function installFakeTimers(t) {
  const intervals = [];
  const cleared = [];
  const originalSetInterval = globalThis.setInterval;
  const originalClearInterval = globalThis.clearInterval;

  globalThis.setInterval = (callback) => {
    intervals.push(callback);
    return intervals.length;
  };
  globalThis.clearInterval = (intervalId) => {
    cleared.push(intervalId);
  };
  t.after(() => {
    RunningApps.unregister();
    router.MainRunningApp = null;
    globalThis.setInterval = originalSetInterval;
    globalThis.clearInterval = originalClearInterval;
  });
  return { intervals, cleared };
}

test("restarts polling and app detection after remount", (t) => {
  const { intervals, cleared } = installFakeTimers(t);
  const firstChanges = [];
  RunningApps.listenActiveChange((newAppId, oldAppId) => {
    firstChanges.push([newAppId, oldAppId]);
  });
  RunningApps.register();
  router.MainRunningApp = { appid: "42" };
  intervals[0]();

  assert.deepEqual(firstChanges, [["42", "0"]]);
  RunningApps.unregister();

  const secondChanges = [];
  RunningApps.listenActiveChange((newAppId, oldAppId) => {
    secondChanges.push([newAppId, oldAppId]);
  });
  RunningApps.register();
  intervals[1]();

  assert.deepEqual(cleared, [1]);
  assert.equal(intervals.length, 2);
  assert.deepEqual(secondChanges, [["42", "0"]]);
});

test("removes listeners by identity after earlier listeners unsubscribe", (t) => {
  const { intervals } = installFakeTimers(t);
  const calls = [];
  const removeFirst = RunningApps.listenActiveChange(() => calls.push("first"));
  const removeSecond = RunningApps.listenActiveChange(() => calls.push("second"));
  RunningApps.listenActiveChange(() => calls.push("third"));

  removeFirst();
  removeSecond();
  RunningApps.register();
  router.MainRunningApp = { appid: "7" };
  intervals[0]();

  assert.deepEqual(calls, ["third"]);
});
