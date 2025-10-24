/**
 * LED Zone Layout Configuration
 * LED 区域布局配置
 * 
 * This file defines the configuration system for mapping LED array indices
 * to physical positions on the device, enabling support for different
 * device layouts (MSI Claw, AyaNeo, etc.)
 * 
 * 此文件定义了将 LED 数组索引映射到设备物理位置的配置系统，
 * 支持不同设备布局（MSI Claw、AyaNeo 等）
 */

/** Physical position of an LED zone */
export type LEDPosition = 
  | "left-top-left"      // 左手柄-上排-左侧
  | "left-top-right"     // 左手柄-上排-右侧
  | "left-bottom-left"   // 左手柄-下排-左侧
  | "left-bottom-right"  // 左手柄-下排-右侧
  | "right-top-left"     // 右手柄-上排-左侧
  | "right-top-right"    // 右手柄-上排-右侧
  | "right-bottom-left"  // 右手柄-下排-左侧
  | "right-bottom-right" // 右手柄-下排-右侧
  | "center-abxy"        // 中间-ABXY键
  | "center-guide";      // 中间-Guide键

/** LED zone mapping configuration */
export interface LEDZoneMapping {
  /** Array index in keyframe data (0-based) */
  arrayIndex: number;
  /** Physical position on device */
  position: LEDPosition;
  /** Short display label (e.g., "R1", "L1") for preview canvas */
  label: string;
  /** Display label i18n key for detailed descriptions */
  labelKey: string;
}

/** Device type identifier */
export type DeviceType = "msi_claw" | "ayaneo_standard" | "ayaneo_kun";

/** Rotation mapping for a stick (4 zones) */
export interface StickRotationMapping {
  /** Clockwise rotation: [from_index] → to_index */
  clockwise: number[];
  /** Counter-clockwise rotation: [from_index] → to_index */
  counterClockwise: number[];
}

/** Complete LED layout configuration for a device */
export interface LEDLayoutConfig {
  /** Device identifier */
  deviceType: DeviceType;
  /** Total number of zones */
  numZones: number;
  /** Zone mappings (arrayIndex → physical position) */
  zoneMappings: LEDZoneMapping[];
  /** Rotation mapping for clockwise/counter-clockwise operations */
  rotationMappings: {
    leftStick: StickRotationMapping;
    rightStick: StickRotationMapping;
  };
}

