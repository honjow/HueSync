import {
  PanelSectionRow,
  DropdownItem,
  gamepadSliderClasses,
  ToggleField,
} from "@decky/ui";
import { FC, useMemo } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { useRgb } from "../hooks";
import { SlowSliderField } from ".";
import { Setting } from "../hooks/settings";

interface ColorControlsProps {
  hue: number;
  saturation: number;
  brightness: number;
  setHsv: (h: number, s: number, v: number, immediate?: boolean) => void;
  supportsColor2?: boolean;
  hue2?: number;
  setHue2?: (h: number, immediate?: boolean) => void;
  onlyBrightness?: boolean;
}

const ColorControls: FC<ColorControlsProps> = ({
  hue,
  saturation,
  brightness,
  setHsv,
  supportsColor2,
  hue2,
  setHue2,
  onlyBrightness,
}) => {
  // 调用更新 RGB 颜色, 放在 onChangeEnd 事件中，避免频繁更新
  const _setHue = (value: number) => {
    setHsv(value, saturation, brightness);
  };

  const _setSaturation = (value: number) => {
    setHsv(hue, value, brightness);
  };

  const _setBrightness = (value: number) => {
    setHsv(hue, saturation, value);
  };

  const setHueValue = (value: number) => {
    setHsv(value, saturation, brightness, false);
  };

  const setSaturationValue = (value: number) => {
    setHsv(hue, value, brightness, false);
  };

  const setBrightnessValue = (value: number) => {
    setHsv(hue, saturation, value, false);
  };

  return (
    <>
      {!onlyBrightness && (
        <>
          <PanelSectionRow>
            <SlowSliderField
              showValue
              label={localizationManager.getString(localizeStrEnum.HUE)}
              value={hue}
              min={0}
              max={359}
              validValues="range"
              bottomSeparator="thick"
              onChangeEnd={_setHue}
              onChange={setHueValue}
              className="ColorPicker_HSlider"
              valueSuffix="°"
            />
          </PanelSectionRow>
          {supportsColor2 && setHue2 && hue2 !== undefined && (
            <PanelSectionRow>
              <SlowSliderField
                showValue
                label={
                  localizationManager.getString(localizeStrEnum.HUE) + " 2"
                }
                value={hue2}
                min={0}
                max={359}
                validValues="range"
                bottomSeparator="thick"
                onChangeEnd={(value) => setHue2(value)}
                onChange={(value) => setHue2(value, false)}
                className="ColorPicker_HSlider2"
                valueSuffix="°"
              />
            </PanelSectionRow>
          )}
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
              onChange={setSaturationValue}
              valueSuffix="%"
              className="ColorPicker_SSlider"
            />
          </PanelSectionRow>
        </>
      )}
      <PanelSectionRow>
        <SlowSliderField
          showValue
          label={localizationManager.getString(localizeStrEnum.BRIGHTNESS)}
          value={brightness}
          min={0}
          max={100}
          onChangeEnd={_setBrightness}
          onChange={setBrightnessValue}
          valueSuffix="%"
          className="ColorPicker_VSlider"
        />
      </PanelSectionRow>
      <style>
        {`
        .ColorPicker_HSlider .${gamepadSliderClasses.SliderTrack},
        .ColorPicker_HSlider2 .${gamepadSliderClasses.SliderTrack} {
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
    </>
  );
};

export const RGBComponent: FC = () => {
  const {
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
  } = useRgb();

  const modes = useMemo(() => {
    return Object.entries(Setting.modeCapabilities).map(([mode]) => ({
      label: localizationManager.getString(
        localizeStrEnum[
          `LED_MODE_${mode.toUpperCase()}` as keyof typeof localizeStrEnum
        ]
      ),
      data: mode,
    }));
  }, []);

  // 获取当前模式的能力
  const currentModeCapabilities = useMemo(() => {
    return (
      Setting.modeCapabilities[rgbMode] || {
        mode: rgbMode,
        color: false,
        color2: false,
        speed: false,
        brightness: false,
      }
    );
  }, [rgbMode]);

  return (
    <>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(
            localizeStrEnum.ENABLE_LED_CONTROL
          )}
          checked={enableControl}
          onChange={(value) => {
            updateEnableControl(value);
          }}
        />
      </PanelSectionRow>
      {enableControl && (
        <>
          <PanelSectionRow>
            <DropdownItem
              label={localizationManager.getString(localizeStrEnum.LED_MODE)}
              strDefaultLabel={localizationManager.getString(
                localizeStrEnum.LED_MODE_DESC
              )}
              selectedOption={modes.find((m) => m.data === rgbMode)?.data}
              rgOptions={modes}
              onChange={(option) => {
                console.log(">>> Dropdown onChange, selected:", option.data);
                if (option.data !== rgbMode) {
                  console.log(">>> Setting new mode:", option.data);
                  updateRgbMode(option.data);
                }
              }}
            />
          </PanelSectionRow>
          {(currentModeCapabilities.color ||
            currentModeCapabilities.brightness) && (
            <ColorControls
              hue={hue}
              saturation={currentModeCapabilities.brightness ? 0 : saturation}
              brightness={brightness}
              setHsv={setHsv}
              supportsColor2={currentModeCapabilities.color2}
              hue2={hue2}
              setHue2={setHue2Value}
              onlyBrightness={currentModeCapabilities.brightness}
            />
          )}
        </>
      )}
    </>
  );
};
