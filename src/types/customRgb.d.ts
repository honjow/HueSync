/**
 * Unified Custom RGB Types
 * 统一的自定义 RGB 类型定义
 * 
 * This file defines the unified data structures for multi-zone custom RGB
 * configurations, used by both MSI (hardware keyframes) and AyaNeo (software animator)
 * devices.
 * 
 * 此文件定义了多区域自定义 RGB 配置的统一数据结构，
 * 用于 MSI（硬件关键帧）和 AyaNeo（软件动画器）设备。
 */

/** RGB color tuple [R, G, B] */
export type RGBTuple = [number, number, number];

/** Device type for multi-zone custom RGB */
export type CustomRgbDeviceType = "msi" | "ayaneo" | "rog_ally";

/** 
 * Unified Custom RGB Configuration
 * 统一的自定义 RGB 配置
 */
export interface CustomRgbConfig {
  /** Speed: 0-20 (higher = faster) */
  speed: number;
  
  /** Brightness: 0-100 (percentage) */
  brightness: number;
  
  /** 
   * Keyframes: [frame_index][zone_index] = [R, G, B]
   * - 1-8 frames
   * - MSI: 9 zones (fixed)
   * - AyaNeo: 8 zones (standard) or 9 zones (KUN)
   */
  keyframes: RGBTuple[][];
}

/** Dictionary of saved custom RGB presets */
export type CustomPresetsDict = Record<string, CustomRgbConfig>;

// Re-export for backward compatibility
export type { RGBTuple as MsiRGBTuple };
export type { CustomRgbConfig as MsiCustomRgbConfig };
export type { CustomPresetsDict as MsiCustomPresetsDict };
export type { CustomRgbConfig as AyaNeoCustomRgbConfig };
export type { CustomPresetsDict as AyaNeoCustomPresetsDict };

