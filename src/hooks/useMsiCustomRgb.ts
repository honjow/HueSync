// MSI Custom RGB React Hook
// MSI 自定义 RGB React Hook

import { useEffect, useState } from "react";
import { MsiCustomRgbSetting } from "./msiCustomRgbSettings";
import { MsiCustomRgbConfig, MsiCustomPresetsDict, RGBTuple } from "../types/msiCustomRgb";

export const useMsiCustomRgb = () => {
  const [presets, setPresets] = useState<MsiCustomPresetsDict>(MsiCustomRgbSetting.presets);
  const [editing, setEditing] = useState<MsiCustomRgbConfig | null>(MsiCustomRgbSetting.currentEditing);
  const [editingName, setEditingName] = useState<string | null>(MsiCustomRgbSetting.currentEditingName);

  useEffect(() => {
    // Initialize and load presets from backend
    MsiCustomRgbSetting.init();
    
    // Listen for preset changes
    const unsubscribe = MsiCustomRgbSetting.onPresetsChange(() => {
      setPresets({ ...MsiCustomRgbSetting.presets });
      setEditing(MsiCustomRgbSetting.currentEditing);
      setEditingName(MsiCustomRgbSetting.currentEditingName);
    });

    return unsubscribe;
  }, []);

  /**
   * Update a specific zone color in a specific frame
   * 更新特定帧中特定区域的颜色
   */
  const updateZoneColor = (frameIdx: number, zoneIdx: number, color: RGBTuple) => {
    if (!editing) return;

    const newConfig = JSON.parse(JSON.stringify(editing)) as MsiCustomRgbConfig;
    newConfig.keyframes[frameIdx][zoneIdx] = color;
    MsiCustomRgbSetting.updateEditingConfig(newConfig);
  };

  /**
   * Add a new keyframe (copy from current or default)
   * 添加新关键帧（从当前复制或使用默认）
   */
  const addKeyframe = (copyFrom?: number) => {
    if (!editing || editing.keyframes.length >= 8) return;

    const newConfig = { ...editing };
    if (copyFrom !== undefined && editing.keyframes[copyFrom]) {
      // Copy from specified frame
      newConfig.keyframes = [
        ...newConfig.keyframes,
        [...editing.keyframes[copyFrom]] as RGBTuple[]
      ];
    } else {
      // Add default black frame
      newConfig.keyframes = [
        ...newConfig.keyframes,
        Array(9).fill([0, 0, 0] as RGBTuple)
      ];
    }
    MsiCustomRgbSetting.updateEditingConfig(newConfig);
  };

  /**
   * Delete a keyframe
   * 删除关键帧
   */
  const deleteKeyframe = (frameIdx: number) => {
    if (!editing || editing.keyframes.length <= 1) return;

    const newConfig = { ...editing };
    newConfig.keyframes = newConfig.keyframes.filter((_, idx) => idx !== frameIdx);
    MsiCustomRgbSetting.updateEditingConfig(newConfig);
  };

  /**
   * Update speed
   * 更新速度
   */
  const updateSpeed = (speed: number) => {
    if (!editing) return;

    const newConfig = { ...editing, speed };
    MsiCustomRgbSetting.updateEditingConfig(newConfig);
  };

  /**
   * Update brightness
   * 更新亮度
   */
  const updateBrightness = (brightness: number) => {
    if (!editing) return;

    const newConfig = { ...editing, brightness };
    MsiCustomRgbSetting.updateEditingConfig(newConfig);
  };

  /**
   * Preview current configuration on device
   * 在设备上预览当前配置
   */
  const preview = async (): Promise<boolean> => {
    return await MsiCustomRgbSetting.previewCurrent();
  };

  /**
   * Save current configuration as a preset
   * 将当前配置保存为预设
   */
  const save = async (name: string): Promise<boolean> => {
    return await MsiCustomRgbSetting.saveCurrent(name);
  };

  /**
   * Start editing a preset
   * 开始编辑预设
   */
  const startEditing = (name?: string) => {
    MsiCustomRgbSetting.startEditing(name);
  };

  /**
   * Cancel editing
   * 取消编辑
   */
  const cancelEditing = () => {
    MsiCustomRgbSetting.cancelEditing();
  };

  /**
   * Delete a preset
   * 删除预设
   */
  const deletePreset = async (name: string): Promise<boolean> => {
    return await MsiCustomRgbSetting.deletePreset(name);
  };

  /**
   * Apply a preset
   * 应用预设
   */
  const applyPreset = async (name: string): Promise<boolean> => {
    return await MsiCustomRgbSetting.applyPreset(name);
  };

  return {
    // State
    presets,
    editing,
    editingName,

    // Editing operations
    updateZoneColor,
    addKeyframe,
    deleteKeyframe,
    updateSpeed,
    updateBrightness,

    // Actions
    preview,
    save,
    startEditing,
    cancelEditing,
    deletePreset,
    applyPreset,
  };
};

