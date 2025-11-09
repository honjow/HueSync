/**
 * LED Layout Configurations
 * LED 布局配置
 * 
 * Defines the physical LED layout for different handheld devices.
 * 定义不同掌机设备的物理 LED 布局。
 * 
 * Visual Parameters:
 * 视觉参数：
 * All visual parameters are optional and will use defaults if not specified.
 * 所有视觉参数都是可选的，如果未指定将使用默认值。
 * 
 * - circles: LED group centers (required)
 *   圆心：LED组的中心位置（必需）
 * - zoneMappings[].radius: Distance from LED to circle center
 *   半径：LED到圆心的距离
 * - visual.ring.innerRadius: Gradient ring inner radius (default: 20)
 *   渐变环内径（默认：20）
 * - visual.ring.outerRadius: Gradient ring outer radius (default: 28)
 *   渐变环外径（默认：28）
 * - visual.led.radius: LED circle radius (default: 8)
 *   LED圆圈半径（默认：8）
 */

import { LEDLayoutConfig, DeviceType, DeviceVariant } from "../types/ledLayout";

/**
 * MSI Claw LED Layout
 * MSI Claw LED 布局
 * 
 * Array indices: 0-7 (sticks), 8 (ABXY)
 * Physical layout (45-degree diagonal positions):
 *   Right stick: R1(0,225°) R2(1,315°) R3(2,45°) R4(3,135°)
 *   Left stick:  L5(4,45°) L6(5,135°) L7(6,225°) L8(7,315°)
 *   Center: ABXY(8)
 */
export const MSI_CLAW_LAYOUT: LEDLayoutConfig = {
  deviceType: "msi_claw",
  numZones: 9,
  
  // Circle centers for LED groups
  circles: {
    leftStick: { x: 80, y: 40 },
    rightStick: { x: 220, y: 40 },
    center: { x: 150, y: 40 }
  },

  visual: {
    ring: { 
      innerRadius: 18,
      outerRadius: 26
    },
    // led: { 
    //   radius: 6,
    //   radiusSelected: 6
    // }
  },
  
  zoneMappings: [
    // Right stick (indices 0-3) - 45° diagonal layout
    { 
      arrayIndex: 0, circle: "rightStick", angle: 225, radius: 38,
      label: { text: "R1", i18nKey: "MSI_LED_ZONE_R1", position: "left" }
    },
    { 
      arrayIndex: 1, circle: "rightStick", angle: 135, radius: 38,
      label: { text: "R2", i18nKey: "MSI_LED_ZONE_R2", position: "right" }
    },
    { 
      arrayIndex: 2, circle: "rightStick", angle: 45, radius: 38,
      label: { text: "R3", i18nKey: "MSI_LED_ZONE_R3", position: "right" }
    },
    { 
      arrayIndex: 3, circle: "rightStick", angle: 315, radius: 38,
      label: { text: "R4", i18nKey: "MSI_LED_ZONE_R4", position: "left" }
    },
    
    // Left stick (indices 4-7) - 45° diagonal layout
    { 
      arrayIndex: 4, circle: "leftStick", angle: 45, radius: 38,
      label: { text: "L5", i18nKey: "MSI_LED_ZONE_L5", position: "right" }
    },
    { 
      arrayIndex: 5, circle: "leftStick", angle: 315, radius: 38,
      label: { text: "L6", i18nKey: "MSI_LED_ZONE_L6", position: "left" }
    },
    { 
      arrayIndex: 6, circle: "leftStick", angle: 225, radius: 38,
      label: { text: "L7", i18nKey: "MSI_LED_ZONE_L7", position: "left" }
    },
    { 
      arrayIndex: 7, circle: "leftStick", angle: 135, radius: 38,
      label: { text: "L8", i18nKey: "MSI_LED_ZONE_L8", position: "right" }
    },
    
    // Center ABXY (index 8)
    { 
      arrayIndex: 8, circle: "center", angle: 0, radius: 0,
      label: { text: "ABXY", i18nKey: "MSI_LED_ZONE_ABXY", position: "bottom" }
    },
  ],
  
  rotationMappings: {
    rightStick: {
      clockwise: [3, 0, 1, 2],
      counterClockwise: [1, 2, 3, 0],
    },
    leftStick: {
      clockwise: [7, 4, 5, 6],
      counterClockwise: [5, 6, 7, 4],
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
 * Cardinal direction layout (0/90/180/270 degrees):
 * 正方位布局（0/90/180/270 度）：
 *   Left stick:  L1(0,90°) L2(1,0°) L3(2,270°) L4(3,180°)
 *   Right stick: R1(4,90°) R2(5,0°) R3(6,270°) R4(7,180°)
 */
export const AYANEO_STANDARD_LAYOUT: LEDLayoutConfig = {
  deviceType: "ayaneo_standard",
  numZones: 8,
  
  // Circle centers for LED groups
  circles: {
    leftStick: { x: 80, y: 40 },
    rightStick: { x: 220, y: 40 }
  },

  visual: {
    ring: { 
      innerRadius: 12,
      outerRadius: 20
    },
    led: { 
      radius: 6,
      radiusSelected: 6
    }
  },
  
  zoneMappings: [
    // Left stick (indices 0-3) - cardinal directions (12/3/6/9 o'clock)
    { 
      arrayIndex: 0, circle: "leftStick", angle: 90, radius: 32,
      label: { text: "L1", i18nKey: "AYANEO_LED_ZONE_L1", position: "bottom" }
    },
    { 
      arrayIndex: 1, circle: "leftStick", angle: 180, radius: 32,
      label: { text: "L2", i18nKey: "AYANEO_LED_ZONE_L2", position: "right" }
    },
    { 
      arrayIndex: 2, circle: "leftStick", angle: 270, radius: 32,
      label: { text: "L3", i18nKey: "AYANEO_LED_ZONE_L3", position: "bottom" }
    },
    { 
      arrayIndex: 3, circle: "leftStick", angle: 0, radius: 32,
      label: { text: "L4", i18nKey: "AYANEO_LED_ZONE_L4", position: "right" }
    },
    
    // Right stick (indices 4-7) - cardinal directions (12/3/6/9 o'clock)
    { 
      arrayIndex: 4, circle: "rightStick", angle: 90, radius: 32,
      label: { text: "R5", i18nKey: "AYANEO_LED_ZONE_R1", position: "bottom" }
    },
    { 
      arrayIndex: 5, circle: "rightStick", angle: 180, radius: 32,
      label: { text: "R6", i18nKey: "AYANEO_LED_ZONE_R2", position: "right" }
    },
    { 
      arrayIndex: 6, circle: "rightStick", angle: 270, radius: 32,
      label: { text: "R7", i18nKey: "AYANEO_LED_ZONE_R3", position: "bottom" }
    },
    { 
      arrayIndex: 7, circle: "rightStick", angle: 0, radius: 32,
      label: { text: "R8", i18nKey: "AYANEO_LED_ZONE_R4", position: "right" }
    },
  ],
  
  rotationMappings: {
    leftStick: {
      clockwise: [1, 2, 3, 0],
      counterClockwise: [3, 0, 1, 2],
    },
    rightStick: {
      clockwise: [5, 6, 7, 4],
      counterClockwise: [7, 4, 5, 6],
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
  
  // Circle centers for LED groups (add center for Guide button)
  circles: {
    leftStick: { x: 70, y: 40 },
    rightStick: { x: 230, y: 40 },
    center: { x: 150, y: 40 }
  },
  
  zoneMappings: [
    ...AYANEO_STANDARD_LAYOUT.zoneMappings,
    // Center Guide button (index 8)
    { 
      arrayIndex: 8, circle: "center", angle: 0, radius: 0,
      label: { text: "Guide", i18nKey: "AYANEO_LED_ZONE_GUIDE", position: "bottom" }
    },
  ],
  
  rotationMappings: AYANEO_STANDARD_LAYOUT.rotationMappings,
};

/**
 * ROG Ally LED Layout (4 zones)
 * ROG Ally LED 布局（4个区域）
 * 
 * Physical layout: Each joystick has 2 LEDs
 * 物理布局：每个摇杆有2个LED
 * 
 */
export const ROG_ALLY_LAYOUT: LEDLayoutConfig = {
  deviceType: "rog_ally",
  variant: "standard",
  numZones: 4,
  
  // Circle centers for LED groups
  circles: {
    leftStick: { x: 80, y: 40 },
    rightStick: { x: 220, y: 40 }
  },

  visual: {
    ring: { 
      innerRadius: 18,
      outerRadius: 26
    },
    led: { 
      radius: 8,
      radiusSelected: 10
    }
  },
  
  zoneMappings: [
    // Left stick
    { 
      arrayIndex: 0, 
      circle: "leftStick", 
      angle: 300,
      radius: 38,
      label: { 
        text: "L1", 
        i18nKey: "ALLY_LED_ZONE_L1", 
        position: "left"
      }
    },
    { 
      arrayIndex: 1, 
      circle: "leftStick", 
      angle: 120,
      radius: 38,
      label: { 
        text: "L2", 
        i18nKey: "ALLY_LED_ZONE_L2", 
        position: "right"
      }
    },
    
    // Right stick
    { 
      arrayIndex: 2, 
      circle: "rightStick", 
      angle: 300,
      radius: 38,
      label: { 
        text: "R3", 
        i18nKey: "ALLY_LED_ZONE_R1", 
        position: "left"
      }
    },
    { 
      arrayIndex: 3, 
      circle: "rightStick", 
      angle: 120,
      radius: 38,
      label: { 
        text: "R4", 
        i18nKey: "ALLY_LED_ZONE_R2", 
        position: "right"
      }
    },
  ],
  
  rotationMappings: {
    leftStick: {
      // L1 ↔ L2 swap
      clockwise: [1, 0],
      counterClockwise: [1, 0],
    },
    rightStick: {
      // R1 ↔ R2 swap
      clockwise: [3, 2],
      counterClockwise: [3, 2],
    },
  },
};

/**
 * ROG Xbox Ally LED Layout (4 zones)
 * ROG Xbox Ally LED 布局（4个区域）
 * 
 * Physical layout differences from standard Ally:
 * 与标准 Ally 的物理布局差异：
 * - Different LED angles/positions
 * - 不同的 LED 角度/位置
 * 
 * Note: Adjust angles based on actual Xbox Ally hardware testing
 * 注意：根据实际 Xbox Ally 硬件测试调整角度
 */
export const ROG_ALLY_XBOX_LAYOUT: LEDLayoutConfig = {
  deviceType: "rog_ally",
  variant: "xbox",
  numZones: 4,
  
  // Circle centers for LED groups (same as standard)
  circles: {
    leftStick: { x: 80, y: 40 },
    rightStick: { x: 220, y: 40 }
  },

  visual: {
    ring: { 
      innerRadius: 18,
      outerRadius: 26
    },
    led: { 
      radius: 8,
      radiusSelected: 10
    }
  },
  
  zoneMappings: [
    // Left stick - adjusted angles for Xbox Ally
    { 
      arrayIndex: 0, 
      circle: "leftStick", 
      angle: 225,
      radius: 38,
      label: { 
        text: "L1", 
        i18nKey: "ALLY_LED_ZONE_L1", 
        position: "left"
      }
    },
    { 
      arrayIndex: 1, 
      circle: "leftStick", 
      angle: 45,
      radius: 38,
      label: { 
        text: "L2", 
        i18nKey: "ALLY_LED_ZONE_L2", 
        position: "right"
      }
    },
    
    // Right stick - adjusted angles for Xbox Ally
    // TODO: Adjust these angles based on actual hardware testing
    { 
      arrayIndex: 2, 
      circle: "rightStick", 
      angle: 45, 
      radius: 38,
      label: { 
        text: "R3", 
        i18nKey: "ALLY_LED_ZONE_R2", 
        position: "right"
      }
    },
    { 
      arrayIndex: 3, 
      circle: "rightStick", 
      angle: 225,
      radius: 38,
      label: { 
        text: "R4", 
        i18nKey: "ALLY_LED_ZONE_R1", 
        position: "left"
      }
    },
  ],
  
  rotationMappings: {
    leftStick: {
      // L1 ↔ L2 swap
      clockwise: [1, 0],
      counterClockwise: [1, 0],
    },
    rightStick: {
      // R1 ↔ R2 swap
      clockwise: [3, 2],
      counterClockwise: [3, 2],
    },
  },
};

/**
 * Get LED layout configuration by device type and variant
 * 根据设备类型和变体获取 LED 布局配置
 * 
 * @param deviceType Device type identifier
 * @param variant Device variant (optional)
 * @returns LED layout configuration
 */
export function getLEDLayout(
  deviceType: DeviceType | string, 
  variant?: DeviceVariant | string
): LEDLayoutConfig {
  switch (deviceType) {
    case "msi_claw":
      return MSI_CLAW_LAYOUT;
    case "ayaneo_standard":
      return AYANEO_STANDARD_LAYOUT;
    case "ayaneo_kun":
      return AYANEO_KUN_LAYOUT;
    case "rog_ally":
      // Return Xbox variant if specified, otherwise standard
      return variant === "xbox" ? ROG_ALLY_XBOX_LAYOUT : ROG_ALLY_LAYOUT;
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
  return layout.zoneMappings.map(m => m.label.i18nKey);
}

