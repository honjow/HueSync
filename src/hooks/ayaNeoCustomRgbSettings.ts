// AyaNeo Custom RGB Settings Management
// AyaNeo 自定义 RGB 设置管理

import { Backend, RGBMode } from "../util";
import { AyaNeoCustomRgbConfig, AyaNeoCustomPresetsDict } from "../types/ayaNeoCustomRgb";
import { Setting } from "./settings";

export class AyaNeoCustomRgbSetting {
  private static _presets: AyaNeoCustomPresetsDict = {};
  private static _currentEditing: AyaNeoCustomRgbConfig | null = null;
  private static _currentEditingName: string | null = null;

  // Event system for preset changes
  private static changeEvent = new EventTarget();

  /**
   * Listen for preset changes
   * 监听预设变化
   */
  static onPresetsChange(callback: () => void): () => void {
    const handler = () => callback();
    this.changeEvent.addEventListener("change", handler);
    return () => this.changeEvent.removeEventListener("change", handler);
  }

  /**
   * Notify all listeners that presets have changed
   * 通知所有监听器预设已变化
   */
  static notifyChange() {
    this.changeEvent.dispatchEvent(new Event("change"));
  }

  /**
   * Initialize - load presets from backend
   * 初始化 - 从后端加载预设
   */
  static async init() {
    try {
      this._presets = await Backend.getAyaNeoCustomPresets();
      this.notifyChange(); // Notify listeners after loading presets
    } catch (error) {
      console.error("Failed to load AyaNeo custom presets:", error);
      this._presets = {};
      this.notifyChange(); // Notify even on error
    }
  }

  /**
   * Get all presets
   * 获取所有预设
   */
  static get presets(): AyaNeoCustomPresetsDict {
    return this._presets;
  }

  /**
   * Get currently editing configuration
   * 获取当前编辑中的配置
   */
  static get currentEditing(): AyaNeoCustomRgbConfig | null {
    return this._currentEditing;
  }

  /**
   * Get currently editing preset name
   * 获取当前编辑的预设名称
   */
  static get currentEditingName(): string | null {
    return this._currentEditingName;
  }

  /**
   * Save a preset
   * 保存预设
   */
  static async savePreset(name: string, config: AyaNeoCustomRgbConfig): Promise<boolean> {
    try {
      const success = await Backend.saveAyaNeoCustomPreset(name, config);
      if (success) {
        this._presets[name] = config;
        this.notifyChange();
      }
      return success;
    } catch (error) {
      console.error(`Failed to save preset '${name}':`, error);
      return false;
    }
  }

  /**
   * Delete a preset
   * 删除预设
   */
  static async deletePreset(name: string): Promise<boolean> {
    try {
      const success = await Backend.deleteAyaNeoCustomPreset(name);
      if (success) {
        delete this._presets[name];
        
        // If this was the currently selected preset, clear it
        if (Setting.currentAyaNeoCustomPreset === name) {
          Setting.currentAyaNeoCustomPreset = "";
        }
        
        this.notifyChange();
      }
      return success;
    } catch (error) {
      console.error(`Failed to delete preset '${name}':`, error);
      return false;
    }
  }

  /**
   * Apply a preset to the device
   * 将预设应用到设备
   */
  static async applyPreset(name: string): Promise<boolean> {
    const config = this._presets[name];
    if (!config) {
      console.error(`Preset '${name}' not found`);
      return false;
    }

    try {
      const success = await Backend.applyAyaNeoCustomPreset(name);
      if (success) {
        Setting.currentAyaNeoCustomPreset = name;
        Setting.mode = RGBMode.ayaneo_custom;
        Setting.saveSettingsData();
        Setting.notifyChange();
      }
      return success;
    } catch (error) {
      console.error(`Failed to apply preset '${name}':`, error);
      return false;
    }
  }

  /**
   * Start editing a preset (existing or new)
   * 开始编辑预设（现有或新建）
   */
  static startEditing(name?: string) {
    if (name && this._presets[name]) {
      // Edit existing preset - deep clone to avoid mutation
      this._currentEditing = JSON.parse(JSON.stringify(this._presets[name]));
      this._currentEditingName = name;
    } else {
      // Create new preset with default configuration
      this._currentEditing = {
        speed: 10,
        brightness: 100,
        keyframes: [
          // Default: all black
          Array(8).fill([0, 0, 0]) as [number, number, number][],
        ],
      };
      this._currentEditingName = null;
    }
    this.notifyChange();
  }

  /**
   * Update current editing configuration
   * 更新当前编辑的配置
   */
  static updateEditing(config: AyaNeoCustomRgbConfig) {
    this._currentEditing = config;
    this.notifyChange();
  }

  /**
   * Save current editing configuration
   * 保存当前编辑的配置
   */
  static async saveCurrent(name: string): Promise<boolean> {
    if (!this._currentEditing) {
      console.error("No configuration is being edited");
      return false;
    }

    const oldName = this._currentEditingName;
    const isRename = oldName && oldName !== name;
    const wasActive = Setting.currentAyaNeoCustomPreset === oldName;

    // Save the new/updated preset
    const success = await this.savePreset(name, this._currentEditing);
    
    if (success) {
      // If renamed, delete the old preset
      if (isRename) {
        await Backend.deleteAyaNeoCustomPreset(oldName);
        delete this._presets[oldName];
        
        // Update current preset reference if it was active
        if (wasActive) {
          Setting.currentAyaNeoCustomPreset = name;
        }
      }
      
      // If the preset was active (either renamed or modified), reapply it
      if (wasActive || Setting.currentAyaNeoCustomPreset === name) {
        await this.applyPreset(name);
      }
      
      this.cancelEditing();
    }
    
    return success;
  }

  /**
   * Cancel editing
   * 取消编辑
   */
  static cancelEditing() {
    this._currentEditing = null;
    this._currentEditingName = null;
    this.notifyChange();
  }

  /**
   * Preview single frame without applying full configuration
   * 预览单帧，不应用完整配置
   */
  static async previewSingleFrame(
    frame: [number, number, number][],
    brightness: number
  ): Promise<boolean> {
    try {
      // Send a temporary configuration with only one frame
      const tempConfig: AyaNeoCustomRgbConfig = {
        speed: 0, // Speed doesn't matter for single frame
        brightness,
        keyframes: [frame],
      };
      
      await Backend.setAyaNeoCustomRgb(tempConfig);
      return true;
    } catch (error) {
      console.error("Failed to preview frame:", error);
      return false;
    }
  }
}

