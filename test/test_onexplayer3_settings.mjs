#!/usr/bin/env node
// Node ESM regression test for the ONEXPLAYER 3 RGB settings model.
// Extracts the real RgbSetting/AppRgbData/SettingsData classes from the
// TypeScript source with the project's installed typescript package.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const require = createRequire(import.meta.url);
const ts = require("typescript");

const sourcePath = fileURLToPath(new URL("../src/hooks/settings.ts", import.meta.url));
const source = readFileSync(sourcePath, "utf8");
const sourceFile = ts.createSourceFile(
  sourcePath,
  source,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TS,
);

const wanted = ["RgbSetting", "AppRgbData", "SettingsData"];
const chunks = [];
const found = [];
for (const statement of sourceFile.statements) {
  if (!ts.isClassDeclaration(statement) || !statement.name) continue;
  const name = statement.name.text;
  if (name === "Setting") break;
  if (!wanted.includes(name)) continue;
  found.push(name);
  const text = source.slice(statement.getStart(sourceFile), statement.getEnd());
  chunks.push(text.replace(/^export\s+/, ""));
}
assert.deepEqual(found, wanted, "expected the settings model classes before Setting");

const compiled = ts.transpileModule(chunks.join("\n\n"), {
  compilerOptions: {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.None,
    useDefineForClassFields: false,
  },
}).outputText;

const sandbox = {
  console: { log() {}, error() {} },
  hsvToRgb: () => [0, 0, 0],
};
const { RgbSetting, AppRgbData, SettingsData } = vm.runInNewContext(
  `${compiled}\n;({ RgbSetting, AppRgbData, SettingsData });`,
  sandbox,
  { filename: "settings-classes.js" },
);

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

function setZones(setting, [hue, saturation, brightness, enabled], primary = true) {
  setting.primaryZoneEnabled = primary;
  setting.rearZoneHue = hue;
  setting.rearZoneSaturation = saturation;
  setting.rearZoneBrightness = brightness;
  setting.rearZoneEnabled = enabled;
  return setting;
}

function assertZones(setting, [hue, saturation, brightness, enabled], primary = true, label = "") {
  assert.equal(setting.primaryZoneEnabled, primary, `${label} primaryZoneEnabled`);
  assert.equal(setting.rearZoneHue, hue, `${label} rearZoneHue`);
  assert.equal(setting.rearZoneSaturation, saturation, `${label} rearZoneSaturation`);
  assert.equal(setting.rearZoneBrightness, brightness, `${label} rearZoneBrightness`);
  assert.equal(setting.rearZoneEnabled, enabled, `${label} rearZoneEnabled`);
}

test("RgbSetting defaults advertise the future zone fields", () => {
  const setting = new RgbSetting();
  assertZones(setting, [0, 100, 100, true], true, "defaults:");
});

test("RgbSetting.deepCopy copies independent zone values including false and zero", () => {
  const source = setZones(new RgbSetting(), [0, 0, 0, false], false);
  const copy = new RgbSetting();
  copy.deepCopy(source);
  assertZones(copy, [0, 0, 0, false], false, "copied:");

  setZones(source, [210, 45, 25, true], true);
  copy.deepCopy(source);
  assertZones(copy, [210, 45, 25, true], true, "recopied:");

  source.rearZoneHue = 300;
  source.primaryZoneEnabled = false;
  assertZones(copy, [210, 45, 25, true], true, "isolated:");
});

test("fromDict keeps the new-zone defaults for old saved profiles", () => {
  const data = new SettingsData();
  data.fromDict({
    perApp: {
      "0": {
        defaultSetting: { mode: "solid", hue: 120, saturation: 100, brightness: 80 },
        acSetting: { mode: "solid", hue: 200, saturation: 100, brightness: 90 },
        batSetting: { mode: "solid", hue: 40, saturation: 100, brightness: 70 },
      },
    },
  });

  assertZones(data.perApp["0"].defaultSetting, [0, 100, 100, true], true, "default:");
  assertZones(data.perApp["0"].acSetting, [0, 100, 100, true], true, "ac:");
  assertZones(data.perApp["0"].batSetting, [0, 100, 100, true], true, "bat:");
});

test("fromDict applies explicitly saved zone fields", () => {
  const data = new SettingsData();
  data.fromDict({
    perApp: {
      "0": {
        defaultSetting: {
          primaryZoneEnabled: false,
          rearZoneHue: 240,
          rearZoneSaturation: 10,
          rearZoneBrightness: 5,
          rearZoneEnabled: false,
        },
      },
    },
  });

  assertZones(data.perApp["0"].defaultSetting, [240, 10, 5, false], false, "loaded:");
});

test("JSON roundtrip preserves per-profile zone fields without leakage", () => {
  const original = new SettingsData();

  const first = new AppRgbData();
  setZones(first.defaultSetting, [10, 20, 30, true], true);
  first.acSetting = setZones(new RgbSetting(), [40, 50, 60, false], false);
  first.batSetting = setZones(new RgbSetting(), [70, 80, 90, true], true);
  first.acStateOverwrite = true;
  original.perApp["0"] = first;

  const second = new AppRgbData();
  setZones(second.defaultSetting, [110, 120, 130, false], false);
  second.batSetting = setZones(new RgbSetting(), [200, 210, 220, true], true);
  original.perApp["777"] = second;

  const reloaded = new SettingsData();
  reloaded.fromDict(JSON.parse(JSON.stringify(original)));

  assertZones(reloaded.perApp["0"].defaultSetting, [10, 20, 30, true], true, "app0 default:");
  assertZones(reloaded.perApp["0"].acSetting, [40, 50, 60, false], false, "app0 ac:");
  assertZones(reloaded.perApp["0"].batSetting, [70, 80, 90, true], true, "app0 bat:");
  assertZones(reloaded.perApp["777"].defaultSetting, [110, 120, 130, false], false, "app777 default:");
  assertZones(reloaded.perApp["777"].batSetting, [200, 210, 220, true], true, "app777 bat:");
  assert.equal(reloaded.perApp["777"].acSetting, null, "app777 ac remains null");

  reloaded.perApp["0"].acSetting.rearZoneHue = 999;
  reloaded.perApp["0"].acSetting.primaryZoneEnabled = true;
  assertZones(reloaded.perApp["0"].defaultSetting, [10, 20, 30, true], true, "no leak default:");
  assertZones(reloaded.perApp["0"].batSetting, [70, 80, 90, true], true, "no leak bat:");
  assertZones(reloaded.perApp["777"].defaultSetting, [110, 120, 130, false], false, "no leak app777:");
});

test("SettingsData.deepCopy deep-copies zone fields per profile", () => {
  const original = new SettingsData();
  const app = new AppRgbData();
  setZones(app.defaultSetting, [15, 25, 35, false], false);
  app.acSetting = setZones(new RgbSetting(), [45, 55, 65, true], true);
  original.perApp["0"] = app;

  const copy = new SettingsData();
  copy.deepCopy(original);

  assertZones(copy.perApp["0"].defaultSetting, [15, 25, 35, false], false, "copy default:");
  assertZones(copy.perApp["0"].acSetting, [45, 55, 65, true], true, "copy ac:");

  original.perApp["0"].defaultSetting.rearZoneHue = 300;
  original.perApp["0"].acSetting.primaryZoneEnabled = false;
  assertZones(copy.perApp["0"].defaultSetting, [15, 25, 35, false], false, "isolated default:");
  assertZones(copy.perApp["0"].acSetting, [45, 55, 65, true], true, "isolated ac:");
});

let failures = 0;
for (const { name, fn } of tests) {
  try {
    fn();
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
