// AyaNeo Custom RGB Settings Management
// AyaNeo 自定义 RGB 设置管理

import { Backend, RGBMode } from "../util";
import { AyaNeoCustomRgbConfig } from "../types/ayaNeoCustomRgb";
import { Setting } from "./settings";
import { createCustomRgbSetting } from "./createCustomRgbSetting";

const AYANEO_DEFAULT_ZONE_COUNT = 8; // Most AyaNeo devices have 8 zones (KUN has 9)

/**
 * AyaNeo Custom RGB Setting class
 * 使用工厂函数创建的 AyaNeo 自定义 RGB 设置类
 */
export const AyaNeoCustomRgbSetting = createCustomRgbSetting<AyaNeoCustomRgbConfig>({
  deviceName: "ayaneo",
  rgbMode: RGBMode.ayaneo_custom,
  backendApi: {
    getPresets: Backend.getAyaNeoCustomPresets.bind(Backend),
    savePreset: Backend.saveAyaNeoCustomPreset.bind(Backend),
    deletePreset: Backend.deleteAyaNeoCustomPreset.bind(Backend),
    applyPreset: Backend.applyAyaNeoCustomPreset.bind(Backend),
    setCustomRgb: Backend.setAyaNeoCustomRgb.bind(Backend),
  },
  defaultZoneCount: AYANEO_DEFAULT_ZONE_COUNT,
  currentPresetGetter: () => Setting.currentAyaNeoCustomPreset,
  currentPresetSetter: (value) => { Setting.currentAyaNeoCustomPreset = value; },
});
