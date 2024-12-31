import { useEffect, useState } from "react";
import { Setting } from ".";
import { Backend, RGBMode } from "../util";

export const useRgb = () => {
  const [hue, setHue] = useState<number>(Setting.getHue());
  const [saturation, setSaturation] = useState<number>(Setting.getSaturation());
  const [brightness, setBrightness] = useState<number>(Setting.getBrightness());

  const [rgbMode, setRgbMode] = useState<RGBMode>(Setting.getMode());

  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.enableControl
  );

  useEffect(() => {
    const getData = async () => {
      // await Setting.loadSettingsData();
      // setHue(Setting.getHue());
      // setSaturation(Setting.getSaturation());
      // setBrightness(Setting.getBrightness());
      // setRgbMode(Setting.getMode());
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
    if (h >= 360) {
      h = 0;
    }
    setHue(h);
    setSaturation(s);
    setBrightness(v);
    Setting.setHue(h);
    Setting.setSaturation(s);
    Setting.setBrightness(v);
    if (apply) {
      await Backend.applySettings();
    }
  };

  const updateRgbMode = async (mode: RGBMode) => {
    setRgbMode(mode);
    Setting.setMode(mode);
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
    updateEnableControl
  };
};
