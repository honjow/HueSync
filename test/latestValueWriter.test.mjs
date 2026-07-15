import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

const sourceUrl = new URL("../src/util/latestValueWriter.ts", import.meta.url);
const source = await readFile(sourceUrl, "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.ESNext,
    target: ts.ScriptTarget.ES2020,
  },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
const { LatestValueWriter } = await import(moduleUrl);

const nextTurn = () => new Promise((resolve) => setImmediate(resolve));

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

test("coalesces same-turn values to the latest snapshot", async () => {
  const writes = [];
  const gate = deferred();
  const writer = new LatestValueWriter(async (value) => {
    writes.push(value);
    await gate.promise;
  });

  const first = writer.enqueue(1);
  const second = writer.enqueue(2);
  const third = writer.enqueue(3);
  await nextTurn();

  assert.deepEqual(writes, [3]);
  gate.resolve();
  await Promise.all([first, second, third]);
});

test("keeps only the latest value while a write is in flight", async () => {
  const writes = [];
  const gates = [];
  const writer = new LatestValueWriter((value) => {
    writes.push(value);
    const gate = deferred();
    gates.push(gate);
    return gate.promise;
  });

  const first = writer.enqueue(1);
  await nextTurn();
  const second = writer.enqueue(2);
  const third = writer.enqueue(3);

  assert.deepEqual(writes, [1]);
  gates[0].resolve();
  await first;
  await nextTurn();
  assert.deepEqual(writes, [1, 3]);

  gates[1].resolve();
  await Promise.all([second, third]);
});

test("snapshots values before later mutations", async () => {
  const writes = [];
  const writer = new LatestValueWriter(
    async (value) => {
      writes.push(value);
    },
    (value) => ({ ...value }),
  );
  const value = { color: "red" };

  const completion = writer.enqueue(value);
  value.color = "blue";
  await completion;

  assert.deepEqual(writes, [{ color: "red" }]);
});

test("recovers after a failed write", async () => {
  const writes = [];
  const writer = new LatestValueWriter(async (value) => {
    writes.push(value);
    if (value === 1) {
      throw new Error("write failed");
    }
  });

  await assert.rejects(writer.enqueue(1), /write failed/);
  await writer.enqueue(2);

  assert.deepEqual(writes, [1, 2]);
});

test("flush waits for the latest queued write", async () => {
  const gate = deferred();
  const writer = new LatestValueWriter(async () => {
    await gate.promise;
  });

  const completion = writer.enqueue(1);
  const flushed = writer.flush();
  let didFlush = false;
  void flushed.then(() => {
    didFlush = true;
  });
  await nextTurn();
  assert.equal(didFlush, false);

  gate.resolve();
  await Promise.all([completion, flushed]);
  assert.equal(didFlush, true);
});
