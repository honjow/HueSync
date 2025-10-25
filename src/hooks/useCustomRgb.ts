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

// Device-specific constants
// 设备特定常量
const DEVICE_CONFIGS = {
  msi: { maxKeyframes: 8, defaultZoneCount: 9 },      // MSI Claw has 9 zones
  ayaneo: { maxKeyframes: 8, defaultZoneCount: 8 },   // Most AyaNeo devices have 8 zones (KUN has 9)
  rog_ally: { maxKeyframes: 8, defaultZoneCount: 4 }, // ROG Ally has 4 zones (2 per joystick)
} as const;

/**
 * Factory function to create a Custom RGB Setting instance
 * 创建自定义 RGB 设置实例的工厂函数
 */
function createDeviceCustomRgbSetting(deviceType: CustomRgbDeviceType) {
  const config = DEVICE_CONFIGS[deviceType];
  return createCustomRgbSetting<CustomRgbConfig>({
    deviceName: deviceType,
    rgbMode: RGBMode.custom,
    backendApi: {
      getPresets: () => Backend.getCustomRgbPresets(deviceType),
      savePreset: (name, cfg) => Backend.saveCustomRgbPreset(deviceType, name, cfg),
      deletePreset: (name) => Backend.deleteCustomRgbPreset(deviceType, name),
      applyPreset: (name) => Backend.applyCustomRgbPreset(deviceType, name),
      setCustomRgb: (cfg) => Backend.setCustomRgb(deviceType, cfg),
    },
    defaultZoneCount: config.defaultZoneCount,
    currentPresetGetter: () => Setting.currentCustomPreset,
    currentPresetSetter: (value) => { Setting.currentCustomPreset = value; },
  });
}

/**
 * Device-specific Custom RGB Setting instances
 * 设备特定的自定义 RGB 设置实例
 * 
 * Exported for direct access in components that need to call Setting methods
 * 导出供需要直接调用 Setting 方法的组件使用
 */
export const MsiCustomRgbSetting = createDeviceCustomRgbSetting("msi");
export const AyaNeoCustomRgbSetting = createDeviceCustomRgbSetting("ayaneo");
export const AllyCustomRgbSetting = createDeviceCustomRgbSetting("rog_ally");

// Create device-specific hook implementations
// 创建设备特定的 hook 实现
const useMsiCustomRgbImpl = createCustomRgbHook<CustomRgbConfig, CustomPresetsDict>(
  MsiCustomRgbSetting,
  DEVICE_CONFIGS.msi
);

const useAyaNeoCustomRgbImpl = createCustomRgbHook<CustomRgbConfig, CustomPresetsDict>(
  AyaNeoCustomRgbSetting,
  DEVICE_CONFIGS.ayaneo
);

const useAllyCustomRgbImpl = createCustomRgbHook<CustomRgbConfig, CustomPresetsDict>(
  AllyCustomRgbSetting,
  DEVICE_CONFIGS.rog_ally
);

/**
 * Unified custom RGB hook that works with any supported device type
 * 适用于任何支持设备类型的统一自定义 RGB hook
 * 
 * This hook automatically returns the correct implementation based on device type.
 * All devices (MSI, AyaNeo, ROG Ally) share the same backend storage.
 * 
 * 此 hook 根据设备类型自动返回正确的实现。
 * 所有设备（MSI、AyaNeo、ROG Ally）共享同一个后端存储。
 * 
 * @returns Hook interface for managing custom RGB
 */
export function useCustomRgb() {
  // All hooks read from the same backend storage (custom_rgb_presets)
  // 所有 hook 从同一个后端存储读取
  const msiHook = useMsiCustomRgbImpl();
  const ayaNeoHook = useAyaNeoCustomRgbImpl();
  const allyHook = useAllyCustomRgbImpl();
  
  // Device hook mapping table
  // 设备 hook 映射表
  const HOOK_MAP = {
    "rog_ally": allyHook,
    "ayaneo": ayaNeoHook,
    "msi": msiHook,
  } as const;
  
  // Determine by device type from capabilities
  // 根据设备能力中的设备类型判断
  // Since all hooks share the same storage, we must select based on device type
  // 由于所有 hook 共享同一存储，必须根据设备类型选择
  const deviceType = Setting.deviceCapabilities?.device_type;
  
  // Return hook from map, default to MSI if unknown
  // 从映射表返回 hook，未知设备默认使用 MSI
  return HOOK_MAP[deviceType as keyof typeof HOOK_MAP] || msiHook;
}

/**
 * Get the zone count for a device type
 * 获取设备类型的区域数量
 */
export function getZoneCountForDevice(deviceType: CustomRgbDeviceType, isKUN?: boolean): number {
  // Special case: AyaNeo KUN has 9 zones instead of 8
  // 特殊情况：AyaNeo KUN 有 9 个 zone 而不是 8 个
  if (deviceType === "ayaneo" && isKUN) {
    return 9;
  }
  
  return DEVICE_CONFIGS[deviceType]?.defaultZoneCount ?? 8; // Default to 8
}

/**
 * Get the max keyframes for all device types
 * 获取所有设备类型的最大关键帧数
 * 
 * Currently all devices (MSI, AyaNeo, ROG Ally) support 1-8 keyframes
 * 目前所有设备（MSI、AyaNeo、ROG Ally）都支持 1-8 个关键帧
 */
export function getMaxKeyframes(): number {
  return 8;
}
