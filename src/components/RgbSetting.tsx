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

  // LED Mode Options (single layer)
  const modeOptions = useMemo(() => {
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

    if (!Setting.deviceCapabilities?.custom_rgb) {
      return baseModes;
    }

    // Custom presets as single-layer options, click to apply directly
    const customPresetModes = Object.keys(presets).map((name) => ({
      label: name,
      data: `msi_custom:${name}`, // Has data property, can maintain focus
    }));

    return [
      ...baseModes,
      ...customPresetModes,
    ];
  }, [presets]);

  // Manage Custom Effects Options (two-level)
  const manageOptions = useMemo(() => {
    if (!Setting.deviceCapabilities?.custom_rgb) {
      return [];
    }

    const options: DropdownOption[] = [
      {
        label: (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
            <FiPlusCircle />
            <span>{localizationManager.getString(localizeStrEnum.MSI_CUSTOM_CREATE_NEW)}</span>
          </div>
        ),
        data: "create_new",
      },
    ];

    if (Object.keys(presets).length > 0) {
      Object.keys(presets).forEach((name) => {
        options.push({
          label: name,
          options: [
            { label: localizationManager.getString(localizeStrEnum.MSI_CUSTOM_EDIT), data: { name, action: "edit" } },
            { label: localizationManager.getString(localizeStrEnum.MSI_CUSTOM_DELETE), data: { name, action: "delete" } },
          ],
        });
      });
    }

    return options;
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

  // Handle mode selection
  const handleModeChange = async (option: DropdownOption) => {
    const selectedData = option.data;
    if (selectedData === "separator") return;

    // Handle custom preset apply
    if (typeof selectedData === 'string' && selectedData.startsWith('msi_custom:')) {
      const presetName = selectedData.replace('msi_custom:', '');
      await applyPreset(presetName);
      return;
    }

    // Handle standard mode change
    if (selectedData !== rgbMode) {
      updateRgbMode(selectedData);
    }
  };

  // Handle manage actions
  const handleManageAction = async (option: DropdownOption) => {
    const selectedData = option.data;
    if (selectedData === "separator") return;

    // Create new effect
    if (selectedData === "create_new") {
      startEditing();
      const modal = showModal(<MsiCustomRgbEditor closeModal={() => modal.Close()} />);
      return;
    }

    // Edit or delete operations
    if (typeof selectedData === 'object' && selectedData !== null && 'action' in selectedData && 'name' in selectedData) {
      const { name, action } = selectedData as { name: string; action: string };
      if (action === "edit") {
        startEditing(name);
        const modal = showModal(<MsiCustomRgbEditor closeModal={() => modal.Close()} />);
      } else if (action === "delete") {
        const success = await deletePreset(name);
        if (!success) {
          alert(`${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_DELETE_FAILED)}: ${name}`);
        }
      }
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
              selectedOption={modeOptions.find((m) => {
                if (rgbMode === RGBMode.msi_custom) {
                  return m.data === `msi_custom:${Setting.currentMsiCustomPreset}`;
                }
                return m.data === rgbMode;
              })?.data}
              rgOptions={modeOptions}
              onChange={handleModeChange}
            />
          </PanelSectionRow>
        )}
        {/* Manage Custom Effects Dropdown */}
        {Setting.deviceCapabilities?.custom_rgb && manageOptions.length > 0 && (
          <PanelSectionRow>
            <DropdownItem
              label={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_MANAGE_EFFECTS)}
              strDefaultLabel={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_SELECT_ACTION)}
              selectedOption={undefined}
              rgOptions={manageOptions}
              onChange={handleManageAction}
            />
          </PanelSectionRow>
        )}
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
