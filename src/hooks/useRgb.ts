import { useEffect, useState } from "react";
import { Setting } from ".";
import { Backend, RGBMode } from "../util";

export const useRgb = () => {
  const [hue, setHue] = useState<number>(Setting.hue);
  const [saturation, setSaturation] = useState<number>(Setting.saturation);
  const [brightness, setBrightness] = useState<number>(Setting.brightness);

  const [rgbMode, setRgbMode] = useState<RGBMode>(Setting.mode);

  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.enableControl
  );

  useEffect(() => {
    const getData = async () => {
      // await Setting.loadSettingsData();
      // setHue(Setting.hue);
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
    // if (h >= 360) {
    //   h = 0;
    // }
    Setting.hue = h;
    Setting.saturation = s;
    Setting.brightness = v;
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
    await Backend.applySettings();
  };

  return {
    hue,
    saturation,
    brightness,
    setHsv,
    rgbMode,
    updateRgbMode,
    enableControl,
    updateEnableControl,
  };
};
