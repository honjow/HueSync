// Generic Custom RGB Setting Factory
// 通用自定义 RGB 设置工厂函数

import { Backend, RGBMode } from "../util";
import { Setting } from "./settings";

type RGBTuple = [number, number, number];

interface CustomRgbConfig {
  speed: number;
  brightness: number;
  keyframes: RGBTuple[][];
}

interface BackendApi<TConfig extends CustomRgbConfig> {
  getPresets: () => Promise<Record<string, TConfig>>;
  savePreset: (name: string, config: TConfig) => Promise<boolean>;
  deletePreset: (name: string) => Promise<boolean>;
  applyPreset: (name: string) => Promise<boolean>;
  setCustomRgb: (config: TConfig) => Promise<boolean>;
}

interface CustomRgbSettingConfig<TConfig extends CustomRgbConfig> {
  deviceName: string; // "msi" or "ayaneo"
  rgbMode: RGBMode; // RGBMode.custom (unified for all devices)
  backendApi: BackendApi<TConfig>;
  defaultZoneCount: number; // Default zone count for new keyframes
  currentPresetGetter: () => string | null;
  currentPresetSetter: (value: string | null) => void;
}

/**
 * Factory function to create custom RGB setting classes
 * 创建自定义 RGB 设置类的工厂函数
 * 
 * This eliminates code duplication between MSI and AyaNeo custom RGB settings
 * 消除 MSI 和 AyaNeo 自定义 RGB 设置之间的代码重复
 */
export function createCustomRgbSetting<TConfig extends CustomRgbConfig>(
  config: CustomRgbSettingConfig<TConfig>
) {
  return class CustomRgbSetting {
    private static _presets: Record<string, TConfig> = {};
    private static _currentEditing: TConfig | null = null;
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
        this._presets = await config.backendApi.getPresets();
        this.notifyChange();
      } catch (error) {
        console.error(`Failed to load ${config.deviceName} custom presets:`, error);
        this._presets = {};
        this.notifyChange();
      }
    }

    /**
     * Get all presets
     * 获取所有预设
     */
    static get presets(): Record<string, TConfig> {
      return this._presets;
    }

    /**
     * Get current editing configuration
     * 获取当前编辑的配置
     */
    static get currentEditing(): TConfig | null {
      return this._currentEditing;
    }

    /**
     * Get current editing name
     * 获取当前编辑的名称
     */
    static get currentEditingName(): string | null {
      return this._currentEditingName;
    }

    /**
     * Save a preset
     * 保存预设
     */
    static async savePreset(name: string, preset: TConfig): Promise<boolean> {
      try {
        const success = await config.backendApi.savePreset(name, preset);
        if (success) {
          this._presets[name] = preset;
          this.notifyChange();
        }
        return success;
      } catch (error) {
        console.error(`Failed to save ${config.deviceName} preset '${name}':`, error);
        return false;
      }
    }

    /**
     * Delete a preset
     * 删除预设
     */
    static async deletePreset(name: string): Promise<boolean> {
      try {
        const success = await config.backendApi.deletePreset(name);
        if (success) {
          delete this._presets[name];
          
          // If this was the currently selected preset, clear it
          if (config.currentPresetGetter() === name) {
            config.currentPresetSetter(null);
            Setting.mode = RGBMode.solid; // Fallback to solid mode
            Setting.saveSettingsData();
            // Reapply settings to device
            await Backend.applySettings();
            Setting.notifyChange();
          }
          
          this.notifyChange();
        }
        return success;
      } catch (error) {
        console.error(`Failed to delete ${config.deviceName} preset '${name}':`, error);
        return false;
      }
    }

    /**
     * Apply a preset to the device
     * 将预设应用到设备
     */
    static async applyPreset(name: string): Promise<boolean> {
      const preset = this._presets[name];
      if (!preset) {
        console.error(`${config.deviceName} preset '${name}' not found`);
        return false;
      }

      try {
        const success = await config.backendApi.applyPreset(name);
        if (success) {
          config.currentPresetSetter(name);
          // Setting.mode setter will automatically call saveSettingsData() and Backend.applySettings()
          // Setting.mode 的 setter 会自动调用 saveSettingsData() 和 Backend.applySettings()
          Setting.mode = config.rgbMode;
          Setting.notifyChange();
        }
        return success;
      } catch (error) {
        console.error(`Failed to apply ${config.deviceName} preset '${name}':`, error);
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
            Array(config.defaultZoneCount).fill([0, 0, 0]) as RGBTuple[],
          ],
        } as TConfig;
        this._currentEditingName = null;
      }
      this.notifyChange();
    }

    /**
     * Update current editing configuration (alias for compatibility)
     * 更新当前编辑的配置（兼容性别名）
     */
    static updateEditingConfig(preset: TConfig) {
      this._currentEditing = preset;
      this.notifyChange();
    }

    /**
     * Update current editing configuration
     * 更新当前编辑的配置
     */
    static updateEditing(preset: TConfig) {
      this._currentEditing = preset;
      this.notifyChange();
    }

    /**
     * Preview current editing configuration on device
     * 在设备上预览当前编辑的配置
     */
    static async previewCurrent(): Promise<boolean> {
      if (!this._currentEditing) {
        return false;
      }
      try {
        return await config.backendApi.setCustomRgb(this._currentEditing);
      } catch (error) {
        console.error(`Failed to preview current ${config.deviceName} config:`, error);
        return false;
      }
    }

    /**
     * Preview single frame from current editing configuration
     * 预览当前编辑配置的单个关键帧
     */
    static async previewSingleFrame(frameIndex: number): Promise<boolean> {
      if (!this._currentEditing || frameIndex >= this._currentEditing.keyframes.length) {
        return false;
      }
      try {
        // Create a config with only the specified frame
        const singleFrameConfig: TConfig = {
          speed: this._currentEditing.speed,
          brightness: this._currentEditing.brightness,
          keyframes: [this._currentEditing.keyframes[frameIndex]],
        } as TConfig;
        
        return await config.backendApi.setCustomRgb(singleFrameConfig);
      } catch (error) {
        console.error(`Failed to preview ${config.deviceName} frame:`, error);
        return false;
      }
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
      const wasActive = config.currentPresetGetter() === oldName;

      // Save the new/updated preset
      const success = await this.savePreset(name, this._currentEditing);
      if (!success) {
        return false;
      }

      // If renaming an existing preset, delete the old one
      if (oldName && oldName !== name) {
        try {
          await config.backendApi.deletePreset(oldName);
          delete this._presets[oldName];
          this.notifyChange();
        } catch (error) {
          console.error(`Failed to delete old ${config.deviceName} preset '${oldName}':`, error);
        }
      }

      // Update current preset name if it was active or is the one being saved
      if (wasActive || config.currentPresetGetter() === name) {
        config.currentPresetSetter(name);
        Setting.saveSettingsData();
        Setting.notifyChange();
      }

      // If the preset was active, reapply it to the device with new configuration
      if (wasActive || config.currentPresetGetter() === name) {
        await this.applyPreset(name);
      }

      return true;
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
  };
}

