/**
 * LED Layout Configurations
 * LED 布局配置
 * 
 * Defines the physical LED layout for different handheld devices.
 * 定义不同掌机设备的物理 LED 布局。
 */

import { LEDLayoutConfig, DeviceType } from "../types/ledLayout";

/**
 * MSI Claw LED Layout
 * MSI Claw LED 布局
 * 
 * Array indices: 0-7 (sticks), 8 (ABXY)
 * Physical layout:
 *   Right stick: R1(0,bottom-left) R2(1,bottom-right) R3(2,top-right) R4(3,top-left)
 *   Left stick:  L5(4,top-right) L6(5,top-left) L7(6,bottom-left) L8(7,bottom-right)
 *   Center: ABXY(8)
 */
export const MSI_CLAW_LAYOUT: LEDLayoutConfig = {
  deviceType: "msi_claw",
  numZones: 9,
  zoneMappings: [
    // Right stick (indices 0-3)
    { arrayIndex: 0, position: "right-bottom-left", labelKey: "MSI_LED_ZONE_R1" },
    { arrayIndex: 1, position: "right-bottom-right", labelKey: "MSI_LED_ZONE_R2" },
    { arrayIndex: 2, position: "right-top-right", labelKey: "MSI_LED_ZONE_R3" },
    { arrayIndex: 3, position: "right-top-left", labelKey: "MSI_LED_ZONE_R4" },
    // Left stick (indices 4-7)
    { arrayIndex: 4, position: "left-top-right", labelKey: "MSI_LED_ZONE_L5" },
    { arrayIndex: 5, position: "left-top-left", labelKey: "MSI_LED_ZONE_L6" },
    { arrayIndex: 6, position: "left-bottom-left", labelKey: "MSI_LED_ZONE_L7" },
    { arrayIndex: 7, position: "left-bottom-right", labelKey: "MSI_LED_ZONE_L8" },
    // Center ABXY (index 8)
    { arrayIndex: 8, position: "center-abxy", labelKey: "MSI_LED_ZONE_ABXY" },
  ],
  rotationMappings: {
    rightStick: {
      // Clockwise: R1→R2, R2→R3, R3→R4, R4→R1
      clockwise: [1, 2, 3, 0],
      // Counter-clockwise: R1→R4, R2→R1, R3→R2, R4→R3
      counterClockwise: [3, 0, 1, 2],
    },
    leftStick: {
      // Clockwise: L5→L6, L6→L7, L7→L8, L8→L5
      // Indices offset by 4: [4]→[5], [5]→[6], [6]→[7], [7]→[4]
      clockwise: [5, 6, 7, 4],
      // Counter-clockwise: L5→L8, L6→L5, L7→L6, L8→L7
      counterClockwise: [7, 4, 5, 6],
    },
  },
};

/**
 * AyaNeo Standard LED Layout (8 zones)
 * AyaNeo 标准 LED 布局（8个区域）
 * 
 * Note: Actual physical layout needs to be verified on real device!
 * 注意：实际物理布局需要在真实设备上验证！
 * 
 * Assumed layout (subject to change based on testing):
 * 假设布局（根据测试结果可能需要调整）：
 *   Left stick:  L1(0,top-left) L2(1,top-right) L3(2,bottom-left) L4(3,bottom-right)
 *   Right stick: R1(4,top-left) R2(5,top-right) R3(6,bottom-left) R4(7,bottom-right)
 */
export const AYANEO_STANDARD_LAYOUT: LEDLayoutConfig = {
  deviceType: "ayaneo_standard",
  numZones: 8,
  zoneMappings: [
    // Left stick (indices 0-3) - assumed order, NEEDS VERIFICATION
    { arrayIndex: 0, position: "left-top-left", labelKey: "AYANEO_LED_ZONE_L1" },
    { arrayIndex: 1, position: "left-top-right", labelKey: "AYANEO_LED_ZONE_L2" },
    { arrayIndex: 2, position: "left-bottom-left", labelKey: "AYANEO_LED_ZONE_L3" },
    { arrayIndex: 3, position: "left-bottom-right", labelKey: "AYANEO_LED_ZONE_L4" },
    // Right stick (indices 4-7) - assumed order, NEEDS VERIFICATION
    { arrayIndex: 4, position: "right-top-left", labelKey: "AYANEO_LED_ZONE_R1" },
    { arrayIndex: 5, position: "right-top-right", labelKey: "AYANEO_LED_ZONE_R2" },
    { arrayIndex: 6, position: "right-bottom-left", labelKey: "AYANEO_LED_ZONE_R3" },
    { arrayIndex: 7, position: "right-bottom-right", labelKey: "AYANEO_LED_ZONE_R4" },
  ],
  rotationMappings: {
    leftStick: {
      // Clockwise: L1→L2, L2→L4, L4→L3, L3→L1
      // top-left → top-right → bottom-right → bottom-left → top-left
      clockwise: [1, 3, 0, 2],
      // Counter-clockwise: L1→L3, L2→L1, L3→L4, L4→L2
      counterClockwise: [2, 0, 3, 1],
    },
    rightStick: {
      // Clockwise: R1→R2, R2→R4, R4→R3, R3→R1
      // Indices offset by 4: [4]→[5], [5]→[7], [7]→[6], [6]→[4]
      clockwise: [5, 7, 4, 6],
      // Counter-clockwise: R1→R3, R2→R1, R3→R4, R4→R2
      counterClockwise: [6, 4, 7, 5],
    },
  },
};

/**
 * AyaNeo KUN LED Layout (9 zones)
 * AyaNeo KUN LED 布局（9个区域，包含Guide键）
 * 
 * Same as standard layout plus center Guide button
 * 与标准布局相同，但增加了中间的 Guide 键
 */
export const AYANEO_KUN_LAYOUT: LEDLayoutConfig = {
  deviceType: "ayaneo_kun",
  numZones: 9,
  zoneMappings: [
    ...AYANEO_STANDARD_LAYOUT.zoneMappings,
    // Center Guide button (index 8)
    { arrayIndex: 8, position: "center-guide", labelKey: "AYANEO_LED_ZONE_GUIDE" },
  ],
  rotationMappings: AYANEO_STANDARD_LAYOUT.rotationMappings,
};

/**
 * Get LED layout configuration by device type
 * 根据设备类型获取 LED 布局配置
 * 
 * @param deviceType Device type identifier
 * @returns LED layout configuration
 */
export function getLEDLayout(deviceType: DeviceType | string): LEDLayoutConfig {
  switch (deviceType) {
    case "msi_claw":
      return MSI_CLAW_LAYOUT;
    case "ayaneo_standard":
      return AYANEO_STANDARD_LAYOUT;
    case "ayaneo_kun":
      return AYANEO_KUN_LAYOUT;
    default:
      // Default to MSI Claw layout
      return MSI_CLAW_LAYOUT;
  }
}

/**
 * Get array of zone label keys for a device type
 * 获取设备类型的区域标签键数组
 * 
 * @param deviceType Device type identifier
 * @returns Array of i18n label keys
 */
export function getZoneLabelKeys(deviceType: DeviceType | string): string[] {
  const layout = getLEDLayout(deviceType);
  return layout.zoneMappings.map(m => m.labelKey);
}

