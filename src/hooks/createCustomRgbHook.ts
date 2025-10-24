// Generic Custom RGB Hook Factory
// 通用自定义 RGB Hook 工厂函数

import { useEffect, useState } from "react";

type RGBTuple = [number, number, number];

interface CustomRgbConfig {
  speed: number;
  brightness: number;
  keyframes: RGBTuple[][];
}

interface CustomRgbSetting<TConfig extends CustomRgbConfig, TPresetsDict> {
  presets: TPresetsDict;
  currentEditing: TConfig | null;
  currentEditingName: string | null;
  init(): Promise<void>;
  onPresetsChange(callback: () => void): () => void;
  updateEditingConfig?(config: TConfig): void;
  updateEditing?(config: TConfig): void;
  previewCurrent(): Promise<boolean>;
  previewSingleFrame(frameIndex: number): Promise<boolean>;
  saveCurrent(name: string): Promise<boolean>;
  startEditing(name?: string): void;
  cancelEditing(): void;
  deletePreset(name: string): Promise<boolean>;
  applyPreset(name: string): Promise<boolean>;
}

interface CustomRgbHookOptions {
  maxKeyframes: number;
  defaultZoneCount: number;
}

/**
 * Factory function to create custom RGB hooks
 * 创建自定义 RGB hook 的工厂函数
 * 
 * This eliminates code duplication between MSI and AyaNeo custom RGB hooks
 * 消除 MSI 和 AyaNeo 自定义 RGB hook 之间的代码重复
 */
export function createCustomRgbHook<TConfig extends CustomRgbConfig, TPresetsDict>(
  Setting: CustomRgbSetting<TConfig, TPresetsDict>,
  options: CustomRgbHookOptions
) {
  return () => {
    const [presets, setPresets] = useState<TPresetsDict>(Setting.presets);
    const [editing, setEditing] = useState<TConfig | null>(Setting.currentEditing);
    const [editingName, setEditingName] = useState<string | null>(Setting.currentEditingName);

    // Subscribe to changes
    useEffect(() => {
      // Initialize and load presets from backend
      Setting.init();
      
      const unsubscribe = Setting.onPresetsChange(() => {
        setPresets({ ...Setting.presets } as TPresetsDict);
        setEditing(Setting.currentEditing);
        setEditingName(Setting.currentEditingName);
      });

      return unsubscribe;
    }, []);

    /**
     * Update a specific zone color in a specific frame
     * 更新特定帧中特定区域的颜色
     */
    const updateZoneColor = (frameIdx: number, zoneIdx: number, color: RGBTuple) => {
      if (!editing) return;

      const newConfig = JSON.parse(JSON.stringify(editing)) as TConfig;
      newConfig.keyframes[frameIdx][zoneIdx] = color;
      
      // Support both updateEditingConfig (MSI) and updateEditing (AyaNeo)
      if (Setting.updateEditingConfig) {
        Setting.updateEditingConfig(newConfig);
      } else if (Setting.updateEditing) {
        Setting.updateEditing(newConfig);
      }
    };

    /**
     * Add a new keyframe (copy from current or default)
     * 添加新关键帧（从当前复制或使用默认）
     */
    const addKeyframe = (copyFrom?: number) => {
      if (!editing || editing.keyframes.length >= options.maxKeyframes) return;
      
      // Determine zone count from first frame or use default
      const zoneCount = editing.keyframes[0]?.length || options.defaultZoneCount;

      const newConfig = { ...editing } as TConfig;
      if (copyFrom !== undefined && editing.keyframes[copyFrom]) {
        // Copy from specified frame
        newConfig.keyframes = [
          ...newConfig.keyframes,
          [...editing.keyframes[copyFrom]] as RGBTuple[]
        ];
      } else {
        // Add default black frame with appropriate zone count
        newConfig.keyframes = [
          ...newConfig.keyframes,
          Array(zoneCount).fill([0, 0, 0] as RGBTuple)
        ];
      }
      
      if (Setting.updateEditingConfig) {
        Setting.updateEditingConfig(newConfig);
      } else if (Setting.updateEditing) {
        Setting.updateEditing(newConfig);
      }
    };

    /**
     * Delete a keyframe
     * 删除关键帧
     */
    const deleteKeyframe = (frameIdx: number) => {
      if (!editing || editing.keyframes.length <= 1) return;

      const newConfig = { ...editing } as TConfig;
      newConfig.keyframes = newConfig.keyframes.filter((_, idx) => idx !== frameIdx);
      
      if (Setting.updateEditingConfig) {
        Setting.updateEditingConfig(newConfig);
      } else if (Setting.updateEditing) {
        Setting.updateEditing(newConfig);
      }
    };

    /**
     * Update speed
     * 更新速度
     */
    const updateSpeed = (speed: number) => {
      if (!editing) return;

      const newConfig = { ...editing, speed } as TConfig;
      
      if (Setting.updateEditingConfig) {
        Setting.updateEditingConfig(newConfig);
      } else if (Setting.updateEditing) {
        Setting.updateEditing(newConfig);
      }
    };

    /**
     * Update brightness
     * 更新亮度
     */
    const updateBrightness = (brightness: number) => {
      if (!editing) return;

      const newConfig = { ...editing, brightness } as TConfig;
      
      if (Setting.updateEditingConfig) {
        Setting.updateEditingConfig(newConfig);
      } else if (Setting.updateEditing) {
        Setting.updateEditing(newConfig);
      }
    };

    /**
     * Preview current configuration on device
     * 在设备上预览当前配置
     */
    const preview = async (): Promise<boolean> => {
      return await Setting.previewCurrent();
    };

    /**
     * Preview a single frame on device
     * 在设备上预览单个关键帧
     */
    const previewSingleFrame = async (frameIndex: number): Promise<boolean> => {
      return await Setting.previewSingleFrame(frameIndex);
    };

    /**
     * Save current configuration as a preset
     * 将当前配置保存为预设
     */
    const save = async (name: string): Promise<boolean> => {
      return await Setting.saveCurrent(name);
    };

    /**
     * Start editing a preset
     * 开始编辑预设
     */
    const startEditing = (name?: string) => {
      Setting.startEditing(name);
    };

    /**
     * Cancel editing
     * 取消编辑
     */
    const cancelEditing = () => {
      Setting.cancelEditing();
    };

    /**
     * Delete a preset
     * 删除预设
     */
    const deletePreset = async (name: string): Promise<boolean> => {
      return await Setting.deletePreset(name);
    };

    /**
     * Apply a preset
     * 应用预设
     */
    const applyPreset = async (name: string): Promise<boolean> => {
      return await Setting.applyPreset(name);
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
      previewSingleFrame,
      save,
      startEditing,
      cancelEditing,
      deletePreset,
      applyPreset,
    };
  };
}

