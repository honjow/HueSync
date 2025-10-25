/**
 * LED Zone Layout Configuration
 * LED 区域布局配置
 * 
 * This file defines the configuration system for mapping LED array indices
 * to physical positions on the device using a circular coordinate system,
 * enabling support for different device layouts (MSI Claw, AyaNeo, etc.)
 * 
 * 此文件定义了使用圆形坐标系统将 LED 数组索引映射到设备物理位置的配置系统，
 * 支持不同设备布局（MSI Claw、AyaNeo 等）
 */

/** Circle center definition */
export interface CircleCenter {
  x: number;
  y: number;
}

/** Circle identifier for LED groups */
export type CircleId = "leftStick" | "rightStick" | "center";

/** Label position relative to LED */
export type LabelPosition = "top" | "bottom" | "left" | "right";

/** LED zone mapping configuration with circular layout */
export interface LEDZoneMapping {
  /** Array index in keyframe data (0-based) */
  arrayIndex: number;
  
  /** Which circle this LED belongs to */
  circle: CircleId;
  
  /** Angle in degrees (0=right, 90=top, 180=left, 270=bottom) */
  angle: number;
  
  /** Radius from circle center */
  radius: number;
  
  /** Label configuration */
  label: {
    /** Short display text (e.g., "R1", "L1") for preview canvas */
    text: string;
    /** Display label i18n key for detailed descriptions */
    i18nKey: string;
    /** Label position relative to LED: "top" | "bottom" | "left" | "right" */
    position: LabelPosition;
    /** Distance from LED center (optional, default: 10-12px) */
    distance?: number;
  };
}

/** Device type identifier */
export type DeviceType = "msi_claw" | "ayaneo_standard" | "ayaneo_kun" | "rog_ally";

/** Rotation mapping for a stick (4 zones) */
export interface StickRotationMapping {
  /** Clockwise rotation: [from_index] → to_index */
  clockwise: number[];
  /** Counter-clockwise rotation: [from_index] → to_index */
  counterClockwise: number[];
}

/** Visual rendering parameters (optional, with sensible defaults) */
export interface VisualParams {
  /** Gradient ring parameters */
  ring?: {
    /** Inner radius of gradient ring (default: 20) */
    innerRadius?: number;
    /** Outer radius of gradient ring (default: 28) */
    outerRadius?: number;
  };
  /** LED circle parameters */
  led?: {
    /** LED circle radius in normal state (default: 8) */
    radius?: number;
    /** LED circle radius when selected (default: 10) */
    radiusSelected?: number;
    /** LED border width in normal state (default: 1) */
    borderWidth?: number;
    /** LED border width when selected (default: 2) */
    borderWidthSelected?: number;
  };
  /** Label text parameters */
  label?: {
    /** Distance from LED center to label in normal state (default: 10) */
    distance?: number;
    /** Distance from LED center to label when selected (default: 12) */
    distanceSelected?: number;
    /** Font size for labels (default: "8px") */
    fontSize?: string;
    /** Font size for LED numbers (default: "bold 8px") */
    fontSizeBold?: string;
  };
}

/** Complete LED layout configuration for a device */
export interface LEDLayoutConfig {
  /** Device identifier */
  deviceType: DeviceType;
  /** Total number of zones */
  numZones: number;
  
  /** Circle centers for different LED groups */
  circles: {
    leftStick: CircleCenter;
    rightStick: CircleCenter;
    center?: CircleCenter;  // Optional, for ABXY/Guide button
  };
  
  /** Zone mappings with circular coordinates */
  zoneMappings: LEDZoneMapping[];
  
  /** Rotation mapping for clockwise/counter-clockwise operations */
  rotationMappings: {
    leftStick: StickRotationMapping;
    rightStick: StickRotationMapping;
  };
  
  /** Optional visual parameters (defaults used if not specified) */
  visual?: VisualParams;
}

