// AyaNeo Custom RGB Hook
// AyaNeo 自定义 RGB Hook

import { useEffect, useState } from "react";
import { AyaNeoCustomRgbSetting } from "./ayaNeoCustomRgbSettings";
import { AyaNeoCustomRgbConfig, AyaNeoCustomPresetsDict } from "../types/ayaNeoCustomRgb";

export const useAyaNeoCustomRgb = () => {
  const [presets, setPresets] = useState<AyaNeoCustomPresetsDict>(AyaNeoCustomRgbSetting.presets);
  const [currentEditing, setCurrentEditing] = useState<AyaNeoCustomRgbConfig | null>(
    AyaNeoCustomRgbSetting.currentEditing
  );
  const [currentEditingName, setCurrentEditingName] = useState<string | null>(
    AyaNeoCustomRgbSetting.currentEditingName
  );

  // Subscribe to changes
  useEffect(() => {
    const unsubscribe = AyaNeoCustomRgbSetting.onPresetsChange(() => {
      setPresets({ ...AyaNeoCustomRgbSetting.presets });
      setCurrentEditing(AyaNeoCustomRgbSetting.currentEditing);
      setCurrentEditingName(AyaNeoCustomRgbSetting.currentEditingName);
    });

    return unsubscribe;
  }, []);

  return {
    presets,
    currentEditing,
    currentEditingName,
    
    // Expose methods
    savePreset: AyaNeoCustomRgbSetting.savePreset.bind(AyaNeoCustomRgbSetting),
    deletePreset: AyaNeoCustomRgbSetting.deletePreset.bind(AyaNeoCustomRgbSetting),
    applyPreset: AyaNeoCustomRgbSetting.applyPreset.bind(AyaNeoCustomRgbSetting),
    startEditing: AyaNeoCustomRgbSetting.startEditing.bind(AyaNeoCustomRgbSetting),
    updateEditing: AyaNeoCustomRgbSetting.updateEditing.bind(AyaNeoCustomRgbSetting),
    saveCurrent: AyaNeoCustomRgbSetting.saveCurrent.bind(AyaNeoCustomRgbSetting),
    cancelEditing: AyaNeoCustomRgbSetting.cancelEditing.bind(AyaNeoCustomRgbSetting),
    previewSingleFrame: AyaNeoCustomRgbSetting.previewSingleFrame.bind(AyaNeoCustomRgbSetting),
  };
};

