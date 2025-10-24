// MSI Custom RGB Settings Management
// MSI 自定义 RGB 设置管理

import { Backend, RGBMode } from "../util";
import { MsiCustomRgbConfig } from "../types/msiCustomRgb";
import { Setting } from "./settings";
import { createCustomRgbSetting } from "./createCustomRgbSetting";

const MSI_ZONE_COUNT = 9; // MSI Claw has 9 zones

/**
 * MSI Custom RGB Setting class
 * 使用工厂函数创建的 MSI 自定义 RGB 设置类
 */
export const MsiCustomRgbSetting = createCustomRgbSetting<MsiCustomRgbConfig>({
  deviceName: "msi",
  rgbMode: RGBMode.msi_custom,
  backendApi: {
    getPresets: Backend.getMsiCustomPresets.bind(Backend),
    savePreset: Backend.saveMsiCustomPreset.bind(Backend),
    deletePreset: Backend.deleteMsiCustomPreset.bind(Backend),
    applyPreset: Backend.applyMsiCustomPreset.bind(Backend),
    setCustomRgb: Backend.setMsiCustomRgb.bind(Backend),
  },
  defaultZoneCount: MSI_ZONE_COUNT,
  currentPresetGetter: () => Setting.currentMsiCustomPreset,
  currentPresetSetter: (value) => { Setting.currentMsiCustomPreset = value; },
});
