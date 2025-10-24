// AyaNeo Custom RGB Hook
// AyaNeo 自定义 RGB Hook

import { AyaNeoCustomRgbSetting } from "./ayaNeoCustomRgbSettings";
import { AyaNeoCustomRgbConfig, AyaNeoCustomPresetsDict } from "../types/ayaNeoCustomRgb";
import { createCustomRgbHook } from "./createCustomRgbHook";

const AYANEO_MAX_KEYFRAMES = 16;
const AYANEO_DEFAULT_ZONE_COUNT = 8; // Most AyaNeo devices have 8 zones (KUN has 9)

/**
 * AyaNeo Custom RGB Hook
 * 使用工厂函数创建的 AyaNeo 自定义 RGB Hook
 */
export const useAyaNeoCustomRgb = createCustomRgbHook<AyaNeoCustomRgbConfig, AyaNeoCustomPresetsDict>(
  AyaNeoCustomRgbSetting,
  {
    maxKeyframes: AYANEO_MAX_KEYFRAMES,
    defaultZoneCount: AYANEO_DEFAULT_ZONE_COUNT,
  }
);

