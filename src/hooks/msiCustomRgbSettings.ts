// MSI Custom RGB Settings Management
// MSI 自定义 RGB 设置管理

import { Backend, RGBMode } from "../util";
import { MsiCustomRgbConfig, MsiCustomPresetsDict } from "../types/msiCustomRgb";
import { Setting } from "./settings";

export class MsiCustomRgbSetting {
  private static _presets: MsiCustomPresetsDict = {};
  private static _currentEditing: MsiCustomRgbConfig | null = null;
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
      this._presets = await Backend.getMsiCustomPresets();
      this.notifyChange(); // Notify listeners after loading presets
    } catch (error) {
      console.error("Failed to load MSI custom presets:", error);
      this._presets = {};
      this.notifyChange(); // Notify even on error
    }
  }

  /**
   * Get all presets
   * 获取所有预设
   */
  static get presets(): MsiCustomPresetsDict {
    return this._presets;
  }

  /**
   * Get currently editing configuration
   * 获取当前编辑中的配置
   */
  static get currentEditing(): MsiCustomRgbConfig | null {
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
  static async savePreset(name: string, config: MsiCustomRgbConfig): Promise<boolean> {
    try {
      const success = await Backend.saveMsiCustomPreset(name, config);
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
      const success = await Backend.deleteMsiCustomPreset(name);
      if (success) {
        delete this._presets[name];
        
        // If deleting the currently applied preset, clear state and switch to default mode
        if (Setting.currentMsiCustomPreset === name) {
          Setting.currentMsiCustomPreset = null;
          Setting.mode = RGBMode.solid; // Fallback to solid mode
          Setting.saveSettingsData();
          // Apply settings to backend/device
          await Backend.applySettings();
          Setting.notifyChange();
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
   * Apply a saved preset
   * 应用保存的预设
   */
  static async applyPreset(name: string): Promise<boolean> {
    try {
      const success = await Backend.applyMsiCustomPreset(name);
      if (success) {
        // Update current preset name and mode in Setting
        Setting.currentMsiCustomPreset = name;
        Setting.mode = RGBMode.msi_custom;
        Setting.saveSettingsData();
        Setting.notifyChange();
        // Apply settings to backend/device
        await Backend.applySettings();
      }
      return success;
    } catch (error) {
      console.error(`Failed to apply preset '${name}':`, error);
      return false;
    }
  }

  /**
   * Start editing (create new or edit existing)
   * 开始编辑（新建或编辑现有）
   */
  static startEditing(name?: string) {
    if (name && this._presets[name]) {
      // Edit existing preset (deep copy)
      this._currentEditing = JSON.parse(JSON.stringify(this._presets[name]));
      this._currentEditingName = name;
    } else {
      // Create new preset
      this._currentEditing = this.createDefaultConfig();
      this._currentEditingName = null;
    }
    this.notifyChange();
  }

  /**
   * Update editing configuration (memory only, not saved)
   * 更新编辑中的配置（仅内存，不保存）
   */
  static updateEditingConfig(config: MsiCustomRgbConfig) {
    this._currentEditing = config;
    this.notifyChange();
  }

  /**
   * Preview current editing configuration (send to device but don't save)
   * 预览当前编辑的配置（发送到设备但不保存）
   */
  static async previewCurrent(): Promise<boolean> {
    if (!this._currentEditing) {
      return false;
    }
    try {
      return await Backend.setMsiCustomRgb(this._currentEditing);
    } catch (error) {
      console.error("Failed to preview current config:", error);
      return false;
    }
  }

  /**
   * Save current editing configuration as a preset
   * 将当前编辑的配置保存为预设
   */
  static async saveCurrent(name: string): Promise<boolean> {
    if (!this._currentEditing) {
      return false;
    }
    
    const oldName = this._currentEditingName;
    const isEditing = oldName !== null; // Editing existing preset
    const isRename = isEditing && oldName !== name; // Renaming
    
    // Save the preset
    const success = await this.savePreset(name, this._currentEditing);
    
    if (success) {
      // Handle rename: delete old preset and update references
      if (isRename) {
        // Update reference if the old preset was currently applied
        if (Setting.currentMsiCustomPreset === oldName) {
          Setting.currentMsiCustomPreset = name;
          Setting.saveSettingsData();
          Setting.notifyChange();
        }
        
        // Delete old preset from backend (direct call to avoid deletePreset's side effects)
        try {
          await Backend.deleteMsiCustomPreset(oldName!);
          delete this._presets[oldName!];
        } catch (error) {
          console.error(`Failed to delete old preset '${oldName}':`, error);
        }
      }
      
      // If editing a currently applied preset (name unchanged or renamed), reapply to device
      if (Setting.currentMsiCustomPreset === name) {
        await this.applyPreset(name);
      }
      
      this._currentEditingName = name;
      this.notifyChange();
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
   * Create default configuration
   * 创建默认配置
   */
  static createDefaultConfig(): MsiCustomRgbConfig {
    // Default: 1 frame, all zones black (ready for user customization)
    return {
      speed: 10,
      brightness: 100,
      keyframes: [
        Array(9).fill([0, 0, 0] as [number, number, number])
      ]
    };
  }
}

