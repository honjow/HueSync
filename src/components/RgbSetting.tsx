import {
  PanelSectionRow,
  PanelSection,
  DropdownItem,
  gamepadSliderClasses,
  ToggleField,
  DropdownOption,
  showModal,
} from "@decky/ui";
import { FC, useMemo } from "react";
import { FiPlusCircle } from "react-icons/fi";
import { localizationManager, localizeStrEnum } from "../i18n";
import { useRgb } from "../hooks";
import { SlowSliderField, SpeedControl, BrightnessLevelControl, MsiCustomRgbEditor } from ".";
import { Setting } from "../hooks/settings";
import { useMsiCustomRgb } from "../hooks";
import { RGBMode } from "../util";

interface ColorControlsProps {
  hue: number;
  saturation: number;
  brightness: number;
  setHsv: (h: number, s: number, v: number, immediate?: boolean) => void;
  supportsColor2?: boolean;
  hue2?: number;
  setHue2?: (h: number, immediate?: boolean) => void;
  onlyBrightness?: boolean;
  zone?: 'primary' | 'secondary';  // New: zone identifier for CSS class names
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
  zone = 'primary',  // Default to primary zone for backward compatibility
}) => {
  // Call to update RGB color, placed in onChangeEnd event to avoid frequent updates | 调用更新 RGB 颜色, 放在 onChangeEnd 事件中，避免频繁更新
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
              className={`ColorPicker_${zone}_HSlider`}
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
                className={`ColorPicker_${zone}_HSlider2`}
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
              className={`ColorPicker_${zone}_SSlider`}
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
          className={`ColorPicker_${zone}_VSlider`}
        />
      </PanelSectionRow>
      <style>
        {`
        .ColorPicker_${zone}_HSlider .${gamepadSliderClasses.SliderTrack},
        .ColorPicker_${zone}_HSlider2 .${gamepadSliderClasses.SliderTrack} {
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
        .ColorPicker_${zone}_SSlider .${gamepadSliderClasses.SliderTrack} {
          background: linear-gradient(
            to right,
            hsl(0, 100%, 100%),
            hsl(${hue}, 100%, 50%)
          ) !important;
          --left-track-color: #0000 !important;
          --colored-toggles-main-color: #0000 !important;
        }
        .ColorPicker_${zone}_VSlider .${gamepadSliderClasses.SliderTrack} {
          background: linear-gradient(
            to right,
            hsl(0, 100%, 0%),
            hsl(${hue}, ${onlyBrightness ? 0 : saturation}%, 50%)
          ) !important;
          --left-track-color: #0000 !important;
          --colored-toggles-main-color: #0000 !important;
        }
      `}
      </style>
    </>
  );
};

enum MSI_PRESET_ACTION {
  ADD = "ADD",
  APPLY = "APPLY",
  EDIT = "EDIT",
  DELETE = "DELETE",
}

export const RGBComponent: FC = () => {
  const {
    hue,
    hue2,
    saturation,
    brightness,
    secondaryZoneHue,
    secondaryZoneSaturation,
    secondaryZoneBrightness,
    secondaryZoneEnabled,
    setHsv,
    setHue2Value,
    setSecondaryZoneHsv,
    updateSecondaryZoneEnabled,
    rgbMode,
    updateRgbMode,
    enableControl,
    updateEnableControl,
    speed,
    updateSpeed,
    brightnessLevel,
    updateBrightnessLevel,
  } = useRgb();

  // MSI Custom RGB hook
  const { presets, startEditing, deletePreset, applyPreset } = useMsiCustomRgb();

  const modes = useMemo(() => {
    // Base preset modes (exclude msi_custom as it will be added dynamically)
    const baseModes = Object.entries(Setting.modeCapabilities)
      .filter(([mode]) => mode !== RGBMode.msi_custom)
      .map(([mode]) => ({
        label: localizationManager.getString(
          localizeStrEnum[
            `LED_MODE_${mode.toUpperCase()}` as keyof typeof localizeStrEnum
          ]
        ),
        data: mode,
      }));

    // If device doesn't support custom RGB, return base modes only
    if (!Setting.deviceCapabilities?.custom_rgb) {
      return baseModes;
    }

    // Custom presets with nested options
    const customPresets = Object.keys(presets).map((name) => ({
      label: name,
      // Note: MultiDropdownOption cannot have 'data' property, only 'options'
      options: [
        {
          label: "Apply",
          data: {
            name,
            type: MSI_PRESET_ACTION.APPLY,
          },
        },
        {
          label: "Edit",
          data: {
            name,
            type: MSI_PRESET_ACTION.EDIT,
          },
        },
        {
          label: "Delete",
          data: {
            name,
            type: MSI_PRESET_ACTION.DELETE,
          },
        },
      ],
    }));

    // Combine: base modes + separator + custom presets + create button
    return [
      ...baseModes,
      ...(customPresets.length > 0 ? [
        {
          label: "────────────────",
          data: "separator",
        }
      ] : []),
      ...customPresets,
      {
        label: (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
            <FiPlusCircle />
            <span>Create Custom Effect</span>
          </div>
        ),
        data: "msi_custom:create_new",
      },
    ];
  }, [presets]);

  // Get current mode capabilities | 获取当前模式的能力
  const currentModeCapabilities = useMemo(() => {
    return (
      Setting.modeCapabilities[rgbMode] || {
        mode: rgbMode,
        color: false,
        color2: false,
        speed: false,
        brightness: false,
        brightness_level: false,
        zones: ['primary'],
      }
    );
  }, [rgbMode]);

  // Check if device has secondary zone and current mode supports it
  // 检查设备是否有副区域且当前模式支持
  const hasSecondaryZone = useMemo(() => {
    return (
      Setting.deviceCapabilities &&
      Setting.deviceCapabilities.zones &&
      Setting.deviceCapabilities.zones.length > 1 &&
      currentModeCapabilities.zones &&
      currentModeCapabilities.zones.includes('secondary')
    );
  }, [currentModeCapabilities]);

  // Get secondary zone name key for i18n
  // 获取副区域名称key用于i18n
  const secondaryZoneNameKey = useMemo(() => {
    if (!Setting.deviceCapabilities?.zones) return null;
    const secondaryZone = Setting.deviceCapabilities.zones.find(z => z.id === 'secondary');
    return secondaryZone?.name_key || null;
  }, []);

  // Handle mode change including custom presets
  const handleModeChange = (option: DropdownOption) => {
    const selectedData = option.data;

    // Ignore separator
    if (selectedData === "separator") {
      return;
    }

    // Handle "Create Custom Effect" button
    if (selectedData === 'msi_custom:create_new') {
      startEditing();
      const createModal = showModal(
        <MsiCustomRgbEditor closeModal={() => createModal.Close()} />
      );
      return;
    }

    // Sub-menu action (Apply/Edit/Delete) - selectedData is an object with name and type
    if (typeof selectedData === 'object' && selectedData !== null && 'type' in selectedData && 'name' in selectedData) {
      const { name, type } = selectedData as { name: string; type: MSI_PRESET_ACTION };
      
      switch (type) {
        case MSI_PRESET_ACTION.APPLY:
          applyPreset(name);
          break;
          
        case MSI_PRESET_ACTION.EDIT:
          startEditing(name);
          const editModal = showModal(
            <MsiCustomRgbEditor closeModal={() => editModal.Close()} />
          );
          break;
          
        case MSI_PRESET_ACTION.DELETE:
          if (confirm(`确认删除预设 "${name}"？\nDelete preset "${name}"?`)) {
            deletePreset(name);
          }
          break;
      }
      return;
    }

    // Standard mode change
    if (selectedData !== rgbMode) {
      updateRgbMode(selectedData);
    }
  };

  // Display mode name
  const displayedModeName = useMemo(() => {
    if (rgbMode === RGBMode.msi_custom) {
      return Setting.currentMsiCustomPreset || "Custom Effect";
    }
    
    return localizationManager.getString(
      localizeStrEnum[`LED_MODE_${rgbMode.toUpperCase()}` as keyof typeof localizeStrEnum]
    );
  }, [rgbMode]);

  return (
    <>
      <PanelSection
        title={localizationManager.getString(localizeStrEnum.RGB_BASIC_SETTINGS)}
      >
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
          <PanelSectionRow>
            <DropdownItem
              label={localizationManager.getString(localizeStrEnum.LED_MODE)}
              strDefaultLabel={displayedModeName}
              selectedOption={modes.find((m) => {
                // If current mode is msi_custom, find the matching preset by label (preset name)
                if (rgbMode === RGBMode.msi_custom) {
                  // Custom presets are MultiDropdownOption with label = preset name
                  return m.label === Setting.currentMsiCustomPreset;
                }
                // Standard modes are SingleDropdownOption with data = mode name
                return 'data' in m && m.data === rgbMode;
              })}
              rgOptions={modes}
              onChange={handleModeChange}
            />
          </PanelSectionRow>)}
      </PanelSection>
      {enableControl && (
        <>
          {/* Primary Zone Section | 主区域设置 */}
          {(currentModeCapabilities.color ||
            currentModeCapabilities.brightness ||
            currentModeCapabilities.speed ||
            currentModeCapabilities.brightness_level) && (
              <PanelSection
                title={localizationManager.getString(localizeStrEnum.ZONE_PRIMARY_NAME)}
              >
                {(currentModeCapabilities.color ||
                  currentModeCapabilities.brightness) && (
                    <ColorControls
                      hue={hue}
                      saturation={saturation}
                      brightness={brightness}
                      setHsv={setHsv}
                      supportsColor2={currentModeCapabilities.color2}
                      hue2={hue2}
                      setHue2={setHue2Value}
                      onlyBrightness={currentModeCapabilities.brightness}
                      zone="primary"
                    />
                  )}
                {currentModeCapabilities.speed && (
                  <PanelSectionRow>
                    <SpeedControl speed={speed} onChange={updateSpeed} />
                  </PanelSectionRow>
                )}
                {currentModeCapabilities.brightness_level && (
                  <PanelSectionRow>
                    <BrightnessLevelControl brightnessLevel={brightnessLevel} onChange={updateBrightnessLevel} />
                  </PanelSectionRow>
                )}
              </PanelSection>
            )}

          {/* Secondary Zone Section | 副区域设置 */}
          {hasSecondaryZone && secondaryZoneNameKey && (
            <PanelSection
              title={localizationManager.getString(
                localizeStrEnum[secondaryZoneNameKey as keyof typeof localizeStrEnum]
              )}
            >
              <PanelSectionRow>
                <ToggleField
                  label={localizationManager.getString(
                    localizeStrEnum.ENABLE_SECONDARY_ZONE
                  )}
                  checked={secondaryZoneEnabled}
                  onChange={(value) => {
                    updateSecondaryZoneEnabled(value);
                  }}
                />
              </PanelSectionRow>
              {secondaryZoneEnabled && (
                <ColorControls
                  hue={secondaryZoneHue}
                  saturation={secondaryZoneSaturation}
                  brightness={secondaryZoneBrightness}
                  setHsv={setSecondaryZoneHsv}
                  supportsColor2={false}
                  onlyBrightness={false}
                  zone="secondary"
                />
              )}
            </PanelSection>
          )}
        </>
      )}
    </>
  );
};
