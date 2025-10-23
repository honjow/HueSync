// MSI Custom RGB Types
// MSI 自定义 RGB 类型定义

/** RGB color tuple [R, G, B] */
export type RGBTuple = [number, number, number];

/** MSI Custom RGB Configuration */
export interface MsiCustomRgbConfig {
  speed: number;           // 0-20 (higher = faster)
  brightness: number;      // 0-100 (percentage)
  keyframes: RGBTuple[][]; // [frame_index][zone_index] = [R, G, B]
                           // 1-8 frames, each with 9 zones
}

/** Dictionary of saved MSI custom presets */
export type MsiCustomPresetsDict = Record<string, MsiCustomRgbConfig>;

