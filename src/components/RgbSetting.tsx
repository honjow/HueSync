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
import { RGBMode } from "../util";
import { Setting } from "../hooks/settings";

export const RGBComponent: FC = () => {
  const {
    hue,
    saturation,
    brightness,
    setHsv,
    rgbMode,
    updateRgbMode,
    enableControl,
    updateEnableControl,
  } = useRgb();

  const modes = useMemo(() => {
    return Object.entries(Setting.modeCapabilities).map(([mode]) => ({
      label: localizationManager.getString(
        localizeStrEnum[`LED_MODE_${mode.toUpperCase()}` as keyof typeof localizeStrEnum]
      ),
      data: mode,
    }));
  }, []);

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

  const setHue = (value: number) => {
    setHsv(value, saturation, brightness, false);
  }

  const setSaturation = (value: number) => {
    setHsv(hue, value, brightness, false);
  }

  const setBrightness = (value: number) => {
    setHsv(hue, saturation, value, false);
  }

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
              strDefaultLabel={localizationManager.getString(localizeStrEnum.LED_MODE_DESC)}
              selectedOption={modes.find(m => m.data === rgbMode)?.data}
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
          {rgbMode == RGBMode.solid && (
            <>
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
            </>
          )}
        </>)}
    </>
  );
};