// AyaNeo Custom RGB Types
// AyaNeo 自定义 RGB 类型定义

import { RGBTuple } from "./msiCustomRgb";

/** AyaNeo Custom RGB Configuration */
export interface AyaNeoCustomRgbConfig {
  speed: number;           // 0-20 (higher = faster)
  brightness: number;      // 0-100 (percentage)
  keyframes: RGBTuple[][]; // [frame_index][zone_index] = [R, G, B]
                           // 1-8 frames, each with 8 or 9 zones (depending on device)
}

/** Dictionary of saved AyaNeo custom presets */
export type AyaNeoCustomPresetsDict = Record<string, AyaNeoCustomRgbConfig>;

