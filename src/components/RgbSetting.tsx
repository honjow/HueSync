import {
  PanelSectionRow,
  PanelSection,
  DropdownItem,
  gamepadSliderClasses,
  ToggleField,
  DropdownOption,
  showModal,
} from "@decky/ui";
import { FC, useMemo, useState } from "react";
import { FiPlusCircle } from "react-icons/fi";
import { localizationManager, localizeStrEnum } from "../i18n";
import { useRgb } from "../hooks";
import { SlowSliderField, SpeedControl, BrightnessLevelControl, CustomRgbEditor } from ".";
import { Setting } from "../hooks/settings";
import { useCustomRgb } from "../hooks";
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
    ledEnabled,
    updateLedEnabled,
    speed,
    updateSpeed,
    brightnessLevel,
    updateBrightnessLevel,
  } = useRgb();

  // Unified Custom RGB hook
  // 统一的自定义 RGB hook
  // Automatically uses the correct implementation (MSI or AyaNeo) based on device data
  // 根据设备数据自动使用正确的实现（MSI 或 AyaNeo）
  const customRgb = useCustomRgb();

  // LED capabilities detection
  // LED 能力检测
  // Get LED capabilities from device capabilities (loaded during initialization)
  // 从设备能力中获取 LED 能力（在初始化时已加载）
  const ledCapabilities = Setting.deviceCapabilities?.led_capabilities || null;
  
  // Local state to track experimental mode (for React reactivity)
  // 本地状态跟踪实验性模式（用于 React 响应）
  const [experimentalEnabled, setExperimentalEnabled] = useState(Setting.experimentalLedEffects);

  // Determine if experimental mode toggle should be shown
  // 判断是否应显示实验性模式开关
  // Show toggle only if device has legacy EC but lacks full sysfs support
  // 仅当设备有慢速 EC 但缺少完整 sysfs 支持时显示开关
  const needsExperimentalMode = ledCapabilities?.is_legacy_ec && ledCapabilities?.ec_access 
    && !(ledCapabilities?.sysfs_single_color && ledCapabilities?.sysfs_multi_zone);

  // Feature availability based on capabilities and experimental setting
  // 基于能力和实验性设置的功能可用性
  const featureAvailability = useMemo(() => {
    if (!ledCapabilities) {
      return {
        softwareEffects: true, // Default: allow all features until capabilities are loaded
        multiFrameCustom: true,
      };
    }

    return {
      // Software effects (Pulse, Rainbow, etc.): available if sysfs single color OR (legacy EC + experimental)
      // 软件灯效：如果支持 sysfs 单色，或（慢速 EC + 实验性模式）
      softwareEffects: ledCapabilities.sysfs_single_color || (needsExperimentalMode && experimentalEnabled),
      // Multi-frame custom animations: available if sysfs multi-zone OR (legacy EC + experimental)
      // 多帧自定义动画：如果支持 sysfs 多区，或（慢速 EC + 实验性模式）
      multiFrameCustom: ledCapabilities.sysfs_multi_zone || (needsExperimentalMode && experimentalEnabled),
    };
  }, [ledCapabilities, experimentalEnabled, needsExperimentalMode]);

  // LED Mode Options (single layer)
  const modeOptions = useMemo(() => {
    // Software effect modes that require feature availability check
    // 需要进行功能可用性检查的软件效果模式
    const softwareEffectModes = [RGBMode.pulse, RGBMode.rainbow, RGBMode.duality, RGBMode.gradient, RGBMode.battery];
    
    // Filter out custom RGB mode from base modes (it will be added as presets)
    // Also filter out software effects if not available
    // 从基础模式中过滤掉自定义 RGB 模式（它将作为预设添加）
    // 如果不可用，也过滤掉软件效果
    const baseModes = Object.entries(Setting.modeCapabilities)
      .filter(([mode]) => {
        if (mode === RGBMode.custom) return false;
        // Filter out disabled mode (now handled by ledEnabled switch)
        // 过滤掉 disabled 模式（现在由 ledEnabled 开关处理）
        if (mode === RGBMode.disabled) return false;
        // Filter out software effects if not available
        // 如果软件效果不可用，则过滤掉
        if (softwareEffectModes.includes(mode as RGBMode) && !featureAvailability.softwareEffects) {
          return false;
        }
        return true;
      })
      .map(([mode]) => ({
        label: localizationManager.getString(
          localizeStrEnum[
            `LED_MODE_${mode.toUpperCase()}` as keyof typeof localizeStrEnum
          ]
        ),
        data: mode,
      }));

    // Add custom presets if device supports custom RGB
    // 如果设备支持自定义 RGB，添加自定义预设
    const customPresetModes = Setting.deviceCapabilities?.custom_rgb
      ? Object.entries(customRgb.presets)
          .filter(([_name, preset]) => {
            // Filter out multi-frame presets if not available
            // 如果不支持多帧，过滤掉多帧预设
            const isMultiFrame = preset.keyframes && preset.keyframes.length > 1;
            if (isMultiFrame && !featureAvailability.multiFrameCustom) {
              return false;
            }
            return true;
          })
          .map(([name]) => ({
            label: name,
            data: `custom:${name}`,
          }))
      : [];

    return [
      ...baseModes,
      ...customPresetModes,
    ];
  }, [customRgb.presets, featureAvailability.softwareEffects, featureAvailability.multiFrameCustom]);

  // Unified Manage Custom Effects Options (two-level)
  // 统一的管理自定义效果选项（两级）
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

    // Add edit/delete options for each preset
    // 为每个预设添加编辑/删除选项
    Object.keys(customRgb.presets).forEach((name) => {
      options.push({
        label: name,
        options: [
          { label: localizationManager.getString(localizeStrEnum.MSI_CUSTOM_EDIT), data: { name, action: "edit" } },
          { label: localizationManager.getString(localizeStrEnum.MSI_CUSTOM_DELETE), data: { name, action: "delete" } },
        ],
      });
    });

    return options;
  }, [customRgb.presets]);

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
    if (typeof selectedData === 'string' && selectedData.startsWith('custom:')) {
      const presetName = selectedData.replace('custom:', '');
      await customRgb.applyPreset(presetName);
      return;
    }

    // Handle standard mode change
    if (selectedData !== rgbMode) {
      updateRgbMode(selectedData);
    }
  };

  // Determine device type from backend capabilities
  // 从后端能力确定设备类型
  const getDeviceType = (): "msi" | "ayaneo" | "rog_ally" => {
    // ALWAYS prioritize backend capabilities
    // 始终优先使用后端能力
    const deviceType = Setting.deviceCapabilities?.device_type;
    
    console.log('[RgbSetting] getDeviceType:', {
      backendDeviceType: deviceType,
      capabilities: Setting.deviceCapabilities,
      presetsCount: Object.keys(customRgb.presets).length
    });
    
    if (deviceType === "rog_ally" || deviceType === "ayaneo" || deviceType === "msi") {
      console.log('[RgbSetting] Using backend device_type:', deviceType);
      return deviceType;
    }
    
    // Fallback: check zone count in presets if device_type not available
    // 备用方案：如果 device_type 不可用，检查预设中的 zone 数量
    const presetKeys = Object.keys(customRgb.presets);
    if (presetKeys.length > 0) {
      const firstPreset = customRgb.presets[presetKeys[0]];
      if (firstPreset && 'keyframes' in firstPreset && firstPreset.keyframes && firstPreset.keyframes[0]) {
        const zoneCount = firstPreset.keyframes[0].length;
        console.log('[RgbSetting] Falling back to zone count detection:', zoneCount);
        // 4 zones = ROG Ally, 8 zones = AyaNeo, 9 zones = MSI
        if (zoneCount === 4) return "rog_ally";
        if (zoneCount === 8) return "ayaneo";
        return "msi";
      }
    }
    
    // This should NEVER happen if backend is working correctly
    // 如果后端正常工作，这不应该发生
    console.error('[RgbSetting] No device type detected! Using MSI as fallback');
    return "msi";
  };

  // Get device variant from backend capabilities
  // 从后端能力获取设备变体
  const getDeviceVariant = (): "standard" | "xbox" => {
    const variant = Setting.deviceCapabilities?.variant;
    console.log('[RgbSetting] getDeviceVariant:', variant);
    return variant === "xbox" ? "xbox" : "standard";
  };

  // Unified handle manage actions
  // 统一的管理操作处理函数
  const handleManageAction = async (option: DropdownOption) => {
    const selectedData = option.data;
    if (selectedData === "separator") return;

    const deviceType = getDeviceType();
    const deviceVariant = getDeviceVariant();

    // Create new effect
    if (selectedData === "create_new") {
      customRgb.startEditing();
      const modal = showModal(
        <CustomRgbEditor 
          closeModal={() => modal.Close()} 
          deviceType={deviceType}
          variant={deviceVariant}
          allowAnimation={featureAvailability.multiFrameCustom}
        />
      );
      return;
    }

    // Edit or delete operations
    if (typeof selectedData === 'object' && selectedData !== null && 'action' in selectedData && 'name' in selectedData) {
      const { name, action } = selectedData as { name: string; action: string };
      if (action === "edit") {
        customRgb.startEditing(name);
        const modal = showModal(
          <CustomRgbEditor 
            closeModal={() => modal.Close()} 
            deviceType={deviceType}
            variant={deviceVariant}
            allowAnimation={featureAvailability.multiFrameCustom}
          />
        );
      } else if (action === "delete") {
        const success = await customRgb.deletePreset(name);
        if (!success) {
          alert(`${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_DELETE_FAILED)}: ${name}`);
        }
      }
    }
  };

  // Display mode name
  const displayedModeName = useMemo(() => {
    // Display custom preset name
    if (rgbMode === RGBMode.custom) {
      return Setting.currentCustomPreset || "Custom Effect";
    }
    
    // Display standard mode name
    return localizationManager.getString(
      localizeStrEnum[`LED_MODE_${rgbMode.toUpperCase()}` as keyof typeof localizeStrEnum]
    );
  }, [rgbMode]);

  // Handle experimental LED effects toggle
  // 处理实验性 LED 效果开关
  const handleExperimentalToggle = async (value: boolean) => {
    Setting.experimentalLedEffects = value;
    setExperimentalEnabled(value); // Update local state to trigger re-render
    
    // If disabling experimental mode, check if current preset is multi-frame
    // 如果禁用实验性模式，检查当前预设是否为多帧
    if (!value && Setting.currentCustomPreset) {
      const currentPreset = customRgb.presets[Setting.currentCustomPreset];
      if (currentPreset && currentPreset.keyframes && currentPreset.keyframes.length > 1) {
        // Current preset is multi-frame and no longer allowed, switch to solid mode
        // 当前预设为多帧且不再允许，切换到纯色模式
        console.log('[RgbSetting] Switching from multi-frame custom to solid mode');
        updateRgbMode(RGBMode.solid);
      }
    }
  };

  return (
    <>
      <PanelSection
        title={localizationManager.getString(localizeStrEnum.RGB_BASIC_SETTINGS)}
      >
        <PanelSectionRow>
          <ToggleField
            label={localizationManager.getString(
              localizeStrEnum.ENABLE_RGB_CONTROL
            )}
            description={localizationManager.getString(
              localizeStrEnum.ENABLE_RGB_CONTROL_DESC
            )}
            checked={enableControl}
            onChange={(value) => {
              updateEnableControl(value);
            }}
          />
        </PanelSectionRow>
        {/* Experimental LED Effects Toggle - only show for legacy EC devices */}
        {/* 实验性 LED 效果开关 - 仅在慢速 EC 设备上显示 */}
        {needsExperimentalMode && (
          <PanelSectionRow>
            <ToggleField
              label={localizationManager.getString(localizeStrEnum.EXPERIMENTAL_LED_EFFECTS)}
              description={localizationManager.getString(localizeStrEnum.EXPERIMENTAL_LED_EFFECTS_DESC)}
              checked={experimentalEnabled}
              onChange={handleExperimentalToggle}
            />
          </PanelSectionRow>
        )}
        {enableControl && (
          <PanelSectionRow>
            <ToggleField
              label={localizationManager.getString(
                localizeStrEnum.LED_SWITCH
              )}
              description={localizationManager.getString(
                localizeStrEnum.LED_SWITCH_DESC
              )}
              checked={ledEnabled}
              onChange={(value) => {
                updateLedEnabled(value);
              }}
            />
          </PanelSectionRow>
        )}
        {enableControl && ledEnabled && (
          <PanelSectionRow>
            <DropdownItem
              label={localizationManager.getString(localizeStrEnum.LIGHTING_EFFECTS)}
              strDefaultLabel={displayedModeName}
              selectedOption={modeOptions.find((m) => {
                if (rgbMode === RGBMode.custom) {
                  return m.data === `custom:${Setting.currentCustomPreset}`;
                }
                return m.data === rgbMode;
              })?.data}
              rgOptions={modeOptions}
              onChange={handleModeChange}
            />
          </PanelSectionRow>
        )}
        {/* Unified Manage Custom Effects Dropdown */}
        {/* 统一的管理自定义效果下拉菜单 */}
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
      {enableControl && ledEnabled && (
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
