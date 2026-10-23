import { useEffect, useState } from "react";
import { Setting } from ".";
import { Backend, RGBMode } from "../util";

export const useRgb = () => {
  const [hue, setHue] = useState<number>(Setting.hue);
  const [hue2, setHue2] = useState<number>(Setting.hue2);
  const [saturation, setSaturation] = useState<number>(Setting.saturation);
  const [brightness, setBrightness] = useState<number>(Setting.brightness);

  const [secondaryZoneHue, setSecondaryZoneHue] = useState<number>(Setting.secondaryZoneHue);
  const [secondaryZoneSaturation, setSecondaryZoneSaturation] = useState<number>(Setting.secondaryZoneSaturation);
  const [secondaryZoneBrightness, setSecondaryZoneBrightness] = useState<number>(Setting.secondaryZoneBrightness);
  const [secondaryZoneEnabled, setSecondaryZoneEnabledState] = useState<boolean>(Setting.secondaryZoneEnabled);

  const [primaryZoneEnabled, setPrimaryZoneEnabled] = useState<boolean>(Setting.primaryZoneEnabled);
  const [rearZoneHue, setRearZoneHue] = useState<number>(Setting.rearZoneHue);
  const [rearZoneSaturation, setRearZoneSaturation] = useState<number>(Setting.rearZoneSaturation);
  const [rearZoneBrightness, setRearZoneBrightness] = useState<number>(Setting.rearZoneBrightness);
  const [rearZoneEnabled, setRearZoneEnabledState] = useState<boolean>(Setting.rearZoneEnabled);

  const [rgbMode, setRgbMode] = useState<RGBMode>(Setting.mode);

  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.enableControl
  );

  const [ledEnabled, setLedEnabled] = useState<boolean>(Setting.ledEnabled);

  const [speed, setSpeed] = useState<string>(Setting.speed);
  const [brightnessLevel, setBrightnessLevel] = useState<string>(Setting.brightnessLevel);

  useEffect(() => {
    // Listen for configuration changes | 监听配置变更
    const unsubscribe = Setting.onSettingChange(() => {
      setHue(Setting.hue);
      setHue2(Setting.hue2);
      setSaturation(Setting.saturation);
      setBrightness(Setting.brightness);
      setSecondaryZoneHue(Setting.secondaryZoneHue);
      setSecondaryZoneSaturation(Setting.secondaryZoneSaturation);
      setSecondaryZoneBrightness(Setting.secondaryZoneBrightness);
      setSecondaryZoneEnabledState(Setting.secondaryZoneEnabled);
      setPrimaryZoneEnabled(Setting.primaryZoneEnabled);
      setRearZoneHue(Setting.rearZoneHue);
      setRearZoneSaturation(Setting.rearZoneSaturation);
      setRearZoneBrightness(Setting.rearZoneBrightness);
      setRearZoneEnabledState(Setting.rearZoneEnabled);
      setRgbMode(Setting.mode);
      setEnableControl(Setting.enableControl);
      setLedEnabled(Setting.ledEnabled);
      setSpeed(Setting.speed);
      setBrightnessLevel(Setting.brightnessLevel);
    });

    return () => {
      unsubscribe();
    };
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

  const updateLedEnabled = async (ledEnabled: boolean) => {
    setLedEnabled(ledEnabled);
    Setting.ledEnabled = ledEnabled;
    await Backend.applySettings();
  };

  const updateSpeed = async (newSpeed: string) => {
    setSpeed(newSpeed);
    Setting.speed = newSpeed;
    await Backend.applySettings();
  };

  const updateBrightnessLevel = async (newBrightnessLevel: string) => {
    setBrightnessLevel(newBrightnessLevel);
    Setting.brightnessLevel = newBrightnessLevel;
    await Backend.applySettings();
  };

  const setSecondaryZoneHsv = async (
    h: number,
    s: number,
    v: number,
    apply: boolean = true
  ) => {
    setSecondaryZoneHue(h);
    setSecondaryZoneSaturation(s);
    setSecondaryZoneBrightness(v);
    Setting.secondaryZoneHue = h;
    Setting.secondaryZoneSaturation = s;
    Setting.secondaryZoneBrightness = v;

    if (apply) {
      await Backend.applySettings();
    }
  };

  const updateSecondaryZoneEnabled = async (enabled: boolean) => {
    setSecondaryZoneEnabledState(enabled);
    Setting.secondaryZoneEnabled = enabled;
    await Backend.applySettings();
  };

  const updatePrimaryZoneEnabled = async (enabled: boolean) => {
    setPrimaryZoneEnabled(enabled);
    Setting.primaryZoneEnabled = enabled;
    await Backend.applySettings();
  };

  const setRearZoneHsv = async (
    h: number,
    s: number,
    v: number,
    apply: boolean = true
  ) => {
    setRearZoneHue(h);
    setRearZoneSaturation(s);
    setRearZoneBrightness(v);
    Setting.rearZoneHue = h;
    Setting.rearZoneSaturation = s;
    Setting.rearZoneBrightness = v;

    if (apply) {
      await Backend.applySettings();
    }
  };

  const updateRearZoneEnabled = async (enabled: boolean) => {
    setRearZoneEnabledState(enabled);
    Setting.rearZoneEnabled = enabled;
    await Backend.applySettings();
  };

  return {
    hue,
    hue2,
    saturation,
    brightness,
    secondaryZoneHue,
    secondaryZoneSaturation,
    secondaryZoneBrightness,
    secondaryZoneEnabled,
    primaryZoneEnabled,
    rearZoneHue,
    rearZoneSaturation,
    rearZoneBrightness,
    rearZoneEnabled,
    setHsv,
    setHue2Value,
    setSecondaryZoneHsv,
    updateSecondaryZoneEnabled,
    setRearZoneHsv,
    updateRearZoneEnabled,
    updatePrimaryZoneEnabled,
    rgbMode,
    updateRgbMode,
    enableControl,
    updateEnableControl,
    ledEnabled,
    updateLedEnabled,
    speed,
    updateSpeed,
    brightnessLevel,
    updateBrightnessLevel,
  };
};
