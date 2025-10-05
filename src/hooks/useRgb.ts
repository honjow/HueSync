import { useEffect, useState } from "react";
import { Setting } from ".";
import { Backend, RGBMode } from "../util";

export const useRgb = () => {
  const [hue, setHue] = useState<number>(Setting.hue);
  const [hue2, setHue2] = useState<number>(Setting.hue2);
  const [saturation, setSaturation] = useState<number>(Setting.saturation);
  const [brightness, setBrightness] = useState<number>(Setting.brightness);

  const [rgbMode, setRgbMode] = useState<RGBMode>(Setting.mode);

  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.enableControl
  );

  const [speed, setSpeed] = useState<string>(Setting.speed);

  useEffect(() => {
    const getData = async () => {
      // await Setting.loadSettingsData();
      // setHue(Setting.hue);
      // setHue2(Setting.hue2);
      // setSaturation(Setting.saturation);
      // setBrightness(Setting.brightness);
      // setRgbMode(Setting.mode);
      // setEnableControl(Setting.enableControl);
    };
    getData();
  }, []);

  const setHsv = async (
    h: number,
    s: number,
    v: number,
    apply: boolean = true
  ) => {
    setHue(h);
    setSaturation(s);
    setBrightness(v);
    Setting.hue = h;

    Setting.saturation = s;
    Setting.brightness = v;

    Setting.saturation2 = s;
    Setting.brightness2 = v;

    if (apply) {
      await Backend.applySettings();
    }
  };

  const setHue2Value = async (
    h: number,
    apply: boolean = true
  ) => {
    setHue2(h);
    Setting.hue2 = h;
    if (apply) {
      await Backend.applySettings();
    }
  };

  const updateRgbMode = async (mode: RGBMode) => {
    setRgbMode(mode);
    Setting.mode = mode;
    await Backend.applySettings();
  };

  const updateEnableControl = async (enableControl: boolean) => {
    setEnableControl(enableControl);
    Setting.enableControl = enableControl;
    await Backend.applySettings({ isInit: true });
  };

  const updateSpeed = async (newSpeed: string) => {
    setSpeed(newSpeed);
    Setting.speed = newSpeed;
    await Backend.applySettings();
  };

  return {
    hue,
    hue2,
    saturation,
    brightness,
    setHsv,
    setHue2Value,
    rgbMode,
    updateRgbMode,
    enableControl,
    updateEnableControl,
    speed,
    updateSpeed,
  };
};
