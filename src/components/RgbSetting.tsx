import {
  PanelSectionRow,
  ToggleField,
  gamepadSliderClasses,
} from "decky-frontend-lib";
import { VFC, useEffect, useState } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { Setting } from "../hooks";
import { SlowSliderField } from ".";

export const RGBComponent: VFC = () => {

  const [hue, setHue] = useState<number>(Setting.getHue());
  const [saturation, setSaturation] = useState<number>(Setting.getSaturation());
  const [brightness, setBrightness] = useState<number>(Setting.getBrightness());

  const [ledOn, setledOn] = useState<boolean>(Setting.getLedOn());

  useEffect(() => {
    // 关联更新三个 slider 的 UI
    setHue(hue);
    setSaturation(saturation);
    setBrightness(brightness);
  }, [hue, saturation, brightness]);

  useEffect(() => {
    Setting.toggleLed(ledOn);
  }, [ledOn]);

  const setHsv = (
    h: number,
    s: number,
    v: number,
    apply: boolean = true
  ) => {
    if (h >= 360) {
      h = 0;
    }

    if (apply) {
      Setting.setHue(h);
      Setting.setSaturation(s);
      Setting.setBrightness(v);
    }
  };

  // 调用更新 RGB 颜色, 放在 onChangeEnd 事件中，避免频繁更新
  const _setHue = (value: number) => {
    setHsv(value, saturation, brightness);
  }

  const _setSaturation = (value: number) => {
    setHsv(hue, value, brightness);
  }

  const _setBrightness = (value: number) => {
    setHsv(hue, saturation, value);
  }

  return (
    <div>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(localizeStrEnum.LED_ON)}
          checked={ledOn}
          onChange={(value) => {
            setledOn(value);
          }}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <SlowSliderField
          showValue
          label={localizationManager.getString(localizeStrEnum.HUE)}
          value={hue}
          min={0}
          max={360}
          validValues="range"
          bottomSeparator="thick"
          onChangeEnd={_setHue}
          onChange={setHue}
          className="ColorPicker_HSlider"
          valueSuffix="°"
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <SlowSliderField
          showValue
          label={localizationManager.getString(localizeStrEnum.SATURATION)}
          value={saturation}
          min={0}
          max={100}
          validValues="range"
          bottomSeparator="thick"
          onChangeEnd={_setSaturation}
          onChange={setSaturation}
          valueSuffix="%"
          className="ColorPicker_SSlider"
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <SlowSliderField
          showValue
          label={localizationManager.getString(localizeStrEnum.BRIGHTNESS)}
          value={brightness}
          min={0}
          max={100}
          onChangeEnd={_setBrightness}
          onChange={setBrightness}
          valueSuffix="%"
          className="ColorPicker_VSlider"
        />
      </PanelSectionRow>
      <style>
        {`
            .ColorPicker_HSlider .${gamepadSliderClasses.SliderTrack} {
              background: linear-gradient(
                to right,
                hsl(0, 100%, 50%),
                hsl(60, 100%, 50%),
                hsl(120, 100%, 50%),
                hsl(180, 100%, 50%),
                hsl(240, 100%, 50%),
                hsl(300, 100%, 50%),
                hsl(360, 100%, 50%)
              ) !important;
              --left-track-color: #0000 !important;
              --colored-toggles-main-color: #0000 !important;
            }
            .ColorPicker_SSlider .${gamepadSliderClasses.SliderTrack} {
              background: linear-gradient(
                to right,
                hsl(0, 100%, 100%),
                hsl(${hue}, 100%, 50%)
              ) !important;
              --left-track-color: #0000 !important;
              --colored-toggles-main-color: #0000 !important;
            }
            .ColorPicker_VSlider .${gamepadSliderClasses.SliderTrack} {
              background: linear-gradient(
                to right,
                hsl(0, 100%, 0%),
                hsl(${hue}, ${saturation}%, 50%)
              ) !important;
              --left-track-color: #0000 !important;
              --colored-toggles-main-color: #0000 !important;
            }
          `}
      </style>
    </div>
  );
};