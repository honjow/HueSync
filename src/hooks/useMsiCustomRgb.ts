// MSI Custom RGB React Hook
// MSI 自定义 RGB React Hook

import { MsiCustomRgbSetting } from "./msiCustomRgbSettings";
import { MsiCustomRgbConfig, MsiCustomPresetsDict } from "../types/msiCustomRgb";
import { createCustomRgbHook } from "./createCustomRgbHook";

const MSI_MAX_KEYFRAMES = 8;
const MSI_ZONE_COUNT = 9; // MSI Claw has 9 zones

/**
 * MSI Custom RGB Hook
 * 使用工厂函数创建的 MSI 自定义 RGB Hook
 */
export const useMsiCustomRgb = createCustomRgbHook<MsiCustomRgbConfig, MsiCustomPresetsDict>(
  MsiCustomRgbSetting,
  {
    maxKeyframes: MSI_MAX_KEYFRAMES,
    defaultZoneCount: MSI_ZONE_COUNT,
  }
);

