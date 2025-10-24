/**
 * Unified Custom RGB Hook
 * 统一的自定义 RGB Hook
 * 
 * This hook provides a unified interface for managing custom RGB configurations
 * across different device types (MSI, AyaNeo, etc.)
 * 
 * 此 hook 为不同设备类型（MSI、AyaNeo 等）的自定义 RGB 配置管理提供统一接口
 */

import { createCustomRgbHook } from './createCustomRgbHook';
import { createCustomRgbSetting } from './createCustomRgbSetting';
import { Backend, RGBMode } from '../util';
import { Setting } from './settings';
import { CustomRgbConfig, CustomPresetsDict, CustomRgbDeviceType } from '../types/customRgb';

const MSI_MAX_KEYFRAMES = 8;
const MSI_ZONE_COUNT = 9; // MSI Claw has 9 zones

const AYANEO_MAX_KEYFRAMES = 8;
const AYANEO_DEFAULT_ZONE_COUNT = 8; // Most AyaNeo devices have 8 zones (KUN has 9)

/**
 * MSI Custom RGB Setting instance
 * MSI 自定义 RGB 设置实例
 * 
 * Exported for direct access in components that need to call Setting methods
 * 导出供需要直接调用 Setting 方法的组件使用
 */
export const MsiCustomRgbSetting = createCustomRgbSetting<CustomRgbConfig>({
  deviceName: "msi",
  rgbMode: RGBMode.custom,
  backendApi: {
    getPresets: () => Backend.getCustomRgbPresets("msi"),
    savePreset: (name, config) => Backend.saveCustomRgbPreset("msi", name, config),
    deletePreset: (name) => Backend.deleteCustomRgbPreset("msi", name),
    applyPreset: (name) => Backend.applyCustomRgbPreset("msi", name),
    setCustomRgb: (config) => Backend.setCustomRgb("msi", config),
  },
  defaultZoneCount: MSI_ZONE_COUNT,
  currentPresetGetter: () => Setting.currentCustomPreset,
  currentPresetSetter: (value) => { Setting.currentCustomPreset = value; },
});

/**
 * AyaNeo Custom RGB Setting instance
 * AyaNeo 自定义 RGB 设置实例
 * 
 * Exported for direct access in components that need to call Setting methods
 * 导出供需要直接调用 Setting 方法的组件使用
 */
export const AyaNeoCustomRgbSetting = createCustomRgbSetting<CustomRgbConfig>({
  deviceName: "ayaneo",
  rgbMode: RGBMode.custom,
  backendApi: {
    getPresets: () => Backend.getCustomRgbPresets("ayaneo"),
    savePreset: (name, config) => Backend.saveCustomRgbPreset("ayaneo", name, config),
    deletePreset: (name) => Backend.deleteCustomRgbPreset("ayaneo", name),
    applyPreset: (name) => Backend.applyCustomRgbPreset("ayaneo", name),
    setCustomRgb: (config) => Backend.setCustomRgb("ayaneo", config),
  },
  defaultZoneCount: AYANEO_DEFAULT_ZONE_COUNT,
  currentPresetGetter: () => Setting.currentCustomPreset,
  currentPresetSetter: (value) => { Setting.currentCustomPreset = value; },
});

// Create device-specific hook implementations
// 创建设备特定的 hook 实现
const useMsiCustomRgbImpl = createCustomRgbHook<CustomRgbConfig, CustomPresetsDict>(
  MsiCustomRgbSetting,
  {
    maxKeyframes: MSI_MAX_KEYFRAMES,
    defaultZoneCount: MSI_ZONE_COUNT,
  }
);

const useAyaNeoCustomRgbImpl = createCustomRgbHook<CustomRgbConfig, CustomPresetsDict>(
  AyaNeoCustomRgbSetting,
  {
    maxKeyframes: AYANEO_MAX_KEYFRAMES,
    defaultZoneCount: AYANEO_DEFAULT_ZONE_COUNT,
  }
);

/**
 * Unified custom RGB hook that works with any supported device type
 * 适用于任何支持设备类型的统一自定义 RGB hook
 * 
 * This hook automatically returns the correct implementation based on device type.
 * Both MSI and AyaNeo share the same backend storage, so only one will have presets at a time.
 * 
 * 此 hook 根据设备类型自动返回正确的实现。
 * MSI 和 AyaNeo 共享同一个后端存储，所以同一时间只有一个会有预设。
 * 
 * @returns Hook interface for managing custom RGB
 */
export function useCustomRgb() {
  // Both hooks read from the same backend storage (custom_rgb_presets)
  // 两个 hook 从同一个后端存储读取
  const msiHook = useMsiCustomRgbImpl();
  const ayaNeoHook = useAyaNeoCustomRgbImpl();
  
  // Determine by actual presets first (if already created)
  // 首先根据实际预设判断（如果已创建）
  if (Object.keys(msiHook.presets).length > 0) return msiHook;
  if (Object.keys(ayaNeoHook.presets).length > 0) return ayaNeoHook;
  
  // If no presets exist, determine by device type from capabilities
  // 如果没有预设，根据设备能力中的设备类型判断
  const deviceType = Setting.deviceCapabilities?.device_type;
  return deviceType === "ayaneo" ? ayaNeoHook : msiHook;
}

/**
 * Get the zone count for a device type
 * 获取设备类型的区域数量
 */
export function getZoneCountForDevice(deviceType: CustomRgbDeviceType, isKUN?: boolean): number {
  if (deviceType === "msi") {
    return 9; // MSI always has 9 zones
  } else if (deviceType === "ayaneo") {
    return isKUN ? 9 : 8; // AyaNeo: 8 (standard) or 9 (KUN)
  }
  return 8; // Default
}

/**
 * Get the max keyframes for all device types
 * 获取所有设备类型的最大关键帧数
 * 
 * Currently all devices (MSI, AyaNeo) support 1-8 keyframes
 * 目前所有设备（MSI、AyaNeo）都支持 1-8 个关键帧
 */
export function getMaxKeyframes(): number {
  return 8;
}
