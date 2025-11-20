import { Setting, SettingsData } from "../hooks";
import { call } from "@decky/api";
import { debounce } from "lodash";
import { Logger, RGBModeCapabilities } from ".";
import { RGBMode } from "./const";

export interface ZoneInfo {
  id: string;
  name_key: string;
}

export interface DeviceCapabilities {
  zones: ZoneInfo[];
  power_led: boolean;
  suspend_mode: boolean;
  custom_rgb?: boolean;  // Multi-zone custom RGB support (MSI, AyaNeo, ROG Ally, etc.)
  device_type?: "msi" | "ayaneo" | "rog_ally" | "generic";  // Device type for custom RGB implementation selection
  variant?: "standard" | "xbox";  // Device variant (e.g., "xbox" for Xbox Ally)
  led_capabilities?: {
    sysfs_single_color: boolean;
    sysfs_multi_zone: boolean;
    ec_access: boolean;
    is_legacy_ec: boolean;
  };
}

interface ApplySettingsOptions {
  isInit?: boolean;
}

interface ApplyColorOptions {
  isInit?: boolean;
  mode?: string;
  red?: number;
  green?: number;
  blue?: number;
  red2?: number;
  green2?: number;
  blue2?: number;
  zoneColors?: {
    secondary?: { r: number; g: number; b: number };
  };
  zoneEnabled?: {
    secondary?: boolean;
  };
  brightness?: number;
  speed?: string;
  brightnessLevel?: string;
}

// Exported callable functions
// export const getVersion = callable<[], string>("get_version");
// export const getLatestVersion = callable<[], string>("get_latest_version");
// export const updateLatest = callable<[], any>("update_latest");

import { getVersionCache, setVersionCache, getStaleCache } from './versionCache';

export class BackendData {
  private current_version = "";
  private latest_version = "";

  public async init() {
    await call<[], string>("get_version").then((result) => {
      console.info("current_version = " + result);
      this.current_version = result;
    });

    // Check cache first to avoid excessive API requests
    // 优先检查缓存以避免过度的 API 请求
    const cache = getVersionCache();
    if (cache) {
      console.info("latest_version (cached) = " + cache.latestVersion);
      this.latest_version = cache.latestVersion;
      return; // Use cache, skip API request / 使用缓存，跳过 API 请求
    }

    // Cache miss or expired, fetch from backend
    // 缓存未命中或过期，从后端获取
    try {
      const result = await call<[], string>("get_latest_version");
      console.info("latest_version (fresh) = " + result);
      this.latest_version = result;
      
      // Save to cache
      // 保存到缓存
      setVersionCache(result);
    } catch (e) {
      console.error("Failed to fetch latest version:", e);
      // If API fails, try to use stale cache
      // API 失败时，尝试使用过期缓存
      const staleCache = getStaleCache();
      if (staleCache) {
        this.latest_version = staleCache.latestVersion;
        console.info("latest_version (stale cache) = " + staleCache.latestVersion);
      }
    }
  }

  public getCurrentVersion() {
    return this.current_version;
  }

  public setCurrentVersion(version: string) {
    this.current_version = version;
  }

  public getLatestVersion() {
    return this.latest_version;
  }

  public setLatestVersion(version: string) {
    this.latest_version = version;
  }
}

export class Backend {
  public static data: BackendData;

  public static async init() {
    this.data = new BackendData();
    await this.data.init();
  }

  private static applyColor(options: ApplyColorOptions = {}) {
    console.log(
      `Applying color: mode=${options.mode} r=${options.red} g=${options.green} b=${options.blue} r2=${options.red2} g2=${options.green2} b2=${options.blue2} zoneColors=${JSON.stringify(options.zoneColors)} init=${options.isInit} brightness=${options.brightness} speed=${options.speed} brightnessLevel=${options.brightnessLevel}`,
    );
    const {
      mode = "disabled",
      red = 0,
      green = 0,
      blue = 0,
      red2 = 0,
      green2 = 0,
      blue2 = 0,
      zoneColors = null,
      zoneEnabled = null,
      isInit = false,
      brightness = 100,
      speed = "low",
      brightnessLevel = "high",
    } = options;
    
    // Convert zoneColors format for backend
    // 将 zoneColors 格式转换为后端格式
    const zoneColorsDict = zoneColors ? {
      secondary: zoneColors.secondary ? {
        R: zoneColors.secondary.r,
        G: zoneColors.secondary.g,
        B: zoneColors.secondary.b,
      } : null,
    } : null;
    
    // Convert zoneEnabled format for backend
    // 将 zoneEnabled 格式转换为后端格式
    const zoneEnabledDict = zoneEnabled ? {
      secondary: zoneEnabled.secondary,
    } : null;
    
    call<
      [
        mode: string,
        r: number,
        g: number,
        b: number,
        r2: number,
        g2: number,
        b2: number,
        init: boolean,
        brightness: number,
        speed: string,
        brightnessLevel: string,
        zoneColors: any,
        zoneEnabled: any,
      ],
      void
    >("set_color", mode, red, green, blue, red2, green2, blue2, isInit, brightness, speed, brightnessLevel, zoneColorsDict, zoneEnabledDict);
  }

  public static throwSuspendEvt() {
    if (!Setting.enableControl) {
      return;
    }
    console.log("throwSuspendEvt");
    // this.serverAPI!.callPluginMethod("setOff", {});
  }

  // suspend
  public static async suspend() {
    if (!Setting.enableControl) {
      return;
    }
    await call("suspend");
  }

  // resume
  public static async resume() {
    if (!Setting.enableControl) {
      return;
    }
    await call("resume");
  }

  // get_suspend_mode
  public static async getSuspendMode(): Promise<string> {
    return (await call("get_suspend_mode")) as string;
  }

  // set_suspend_mode
  public static async setSuspendMode(mode: string) {
    await call("set_suspend_mode", mode);
  }

  public static async getLatestVersion(): Promise<string> {
    return (await call("get_latest_version")) as string;
  }

  // updateLatest
  public static async updateLatest() {
    await call("update_latest");
  }

  // is_support_suspend_mode
  public static async isSupportSuspendMode(): Promise<boolean> {
    return (await call("is_support_suspend_mode")) as boolean;
  }

  // get_device_capabilities
  public static async getDeviceCapabilities(): Promise<DeviceCapabilities> {
    return (await call("get_device_capabilities")) as DeviceCapabilities;
  }

  // get_mode_capabilities
  public static async getModeCapabilities(): Promise<Record<string, RGBModeCapabilities>> {
    return (await call("get_mode_capabilities")) as Record<string, RGBModeCapabilities>;
  }

  private static _applySettings = ({ isInit = false }: ApplySettingsOptions = {}) => {
    if (!Setting.enableControl) {
      return;
    }

    // Calculate actual mode based on ledEnabled state
    // 根据 ledEnabled 状态计算实际模式
    const actualMode = Setting.ledEnabled ? Setting.mode : RGBMode.disabled;

    // Handle custom RGB mode separately
    // 自定义 RGB 模式单独处理
    if (Setting.mode === RGBMode.custom && Setting.ledEnabled) {
      const deviceType = Setting.deviceCapabilities?.device_type;
      const presetName = Setting.currentCustomPreset;
      
      if (deviceType && presetName) {
        Logger.info(`Applying custom preset '${presetName}' for device '${deviceType}'`);
        Backend.applyCustomRgbPreset(deviceType, presetName);
      } else {
        Logger.warn(`Custom mode active but missing info: deviceType=${deviceType}, preset=${presetName}`);
      }
      return; // Don't continue with standard mode logic
    }

    if (Setting.isSupportSuspendMode) {
      Logger.info(`HueSync: set suspend mode [${Setting.suspendMode}]`);
      Backend.setSuspendMode(Setting.suspendMode);
    }

    // Only construct zone parameters if device supports secondary zone
    // 只有设备支持副区域时才构造区域参数
    const hasSecondaryZone = Setting.deviceCapabilities?.zones?.some(z => z.id === 'secondary');

    const zoneColors = hasSecondaryZone &&
                       Setting.secondaryZoneRed !== undefined && 
                       Setting.secondaryZoneGreen !== undefined && 
                       Setting.secondaryZoneBlue !== undefined
      ? {
          secondary: {
            r: Setting.secondaryZoneRed,
            g: Setting.secondaryZoneGreen,
            b: Setting.secondaryZoneBlue,
          },
        }
      : undefined;

    const zoneEnabled = hasSecondaryZone
      ? {
          secondary: Setting.secondaryZoneEnabled,
        }
      : undefined;

    Backend.applyColor({
      mode: actualMode,
      red: Setting.red,
      green: Setting.green,
      blue: Setting.blue,
      red2: Setting.red2,
      green2: Setting.green2,
      blue2: Setting.blue2,
      zoneColors,
      zoneEnabled,
      isInit,
      brightness: Setting.brightness,
      speed: Setting.speed,
      brightnessLevel: Setting.brightnessLevel,
    });

  };

  // Use debounce with 300ms delay | 使用防抖，延迟 300ms
  public static applySettings = debounce(Backend._applySettings, 300);

  // get_settings
  public static async getSettings(): Promise<SettingsData> {
    const res = (await call("get_settings")) as Record<string, unknown>;
    if (!res) {
      return new SettingsData();
    }
    console.log(`get_settings: ${JSON.stringify(res)}`);
    let data = new SettingsData();
    data.fromDict(res as Record<string, unknown>);
    return data;
  }

  // set_settings
  public static async setSettings(settings: SettingsData) {
    return await call("set_settings", settings);
  }

  // set_power_light
  public static async setPowerLight(enabled: boolean): Promise<boolean> {
    return (await call("set_power_light", enabled)) as boolean;
  }

  // get_power_light
  public static async getPowerLight(): Promise<boolean | null> {
    return (await call("get_power_light")) as boolean | null;
  }

  // log_info
  public static logInfo(message: string) {
    return call("log_info", message);
  }

  // log_error
  public static logError(message: string) {
    return call("log_error", message);
  }

  // log_warn
  public static logWarn(message: string) {
    return call("log_warn", message);
  }

  // log_debug
  public static logDebug(message: string) {
    return call("log_debug", message);
  }

  // ===== Unified Custom RGB API =====
  // 统一的自定义 RGB API
  // Device-agnostic interface for multi-zone custom RGB
  // 设备无关的多区域自定义 RGB 接口

  /**
   * Get all custom RGB presets for any device type
   * 获取任何设备类型的所有自定义 RGB 预设
   */
  public static async getCustomRgbPresets(deviceType: string): Promise<Record<string, any>> {
    return (await call("get_custom_rgb_presets", deviceType)) as Record<string, any>;
  }

  /**
   * Save a custom RGB preset for any device type
   * 为任何设备类型保存自定义 RGB 预设
   */
  public static async saveCustomRgbPreset(deviceType: string, name: string, config: any): Promise<boolean> {
    return (await call("save_custom_rgb_preset", deviceType, name, config)) as boolean;
  }

  /**
   * Delete a custom RGB preset for any device type
   * 删除任何设备类型的自定义 RGB 预设
   */
  public static async deleteCustomRgbPreset(deviceType: string, name: string): Promise<boolean> {
    return (await call("delete_custom_rgb_preset", deviceType, name)) as boolean;
  }

  /**
   * Apply a custom RGB preset for any device type
   * 应用任何设备类型的自定义 RGB 预设
   */
  public static async applyCustomRgbPreset(deviceType: string, name: string): Promise<boolean> {
    return (await call("apply_custom_rgb_preset", deviceType, name)) as boolean;
  }

  /**
   * Apply custom RGB configuration for any device type
   * 为任何设备类型应用自定义 RGB 配置
   */
  public static async setCustomRgb(deviceType: string, config: any): Promise<boolean> {
    return (await call("set_custom_rgb", deviceType, config)) as boolean;
  }

  // ===== MSI Custom RGB Methods (Legacy - Use unified API above) =====
  // MSI 自定义 RGB 方法（旧版 - 请使用上方的统一 API）

  // get_msi_custom_presets
  public static async getMsiCustomPresets(): Promise<Record<string, any>> {
    return await this.getCustomRgbPresets("msi");
  }

  // save_msi_custom_preset
  public static async saveMsiCustomPreset(name: string, config: any): Promise<boolean> {
    return await this.saveCustomRgbPreset("msi", name, config);
  }

  // delete_msi_custom_preset
  public static async deleteMsiCustomPreset(name: string): Promise<boolean> {
    return await this.deleteCustomRgbPreset("msi", name);
  }

  // apply_msi_custom_preset
  public static async applyMsiCustomPreset(name: string): Promise<boolean> {
    return await this.applyCustomRgbPreset("msi", name);
  }

  // set_msi_custom_rgb
  public static async setMsiCustomRgb(config: any): Promise<boolean> {
    return await this.setCustomRgb("msi", config);
  }

  // ===== AyaNeo Custom RGB Methods (Legacy - Use unified API above) =====
  // AyaNeo 自定义 RGB 方法（旧版 - 请使用上方的统一 API）

  // get_ayaneo_custom_presets
  public static async getAyaNeoCustomPresets(): Promise<any> {
    return await this.getCustomRgbPresets("ayaneo");
  }

  // save_ayaneo_custom_preset
  public static async saveAyaNeoCustomPreset(name: string, config: any): Promise<boolean> {
    return await this.saveCustomRgbPreset("ayaneo", name, config);
  }

  // delete_ayaneo_custom_preset
  public static async deleteAyaNeoCustomPreset(name: string): Promise<boolean> {
    return await this.deleteCustomRgbPreset("ayaneo", name);
  }

  // apply_ayaneo_custom_preset
  public static async applyAyaNeoCustomPreset(name: string): Promise<boolean> {
    return await this.applyCustomRgbPreset("ayaneo", name);
  }

  // set_ayaneo_custom_rgb
  public static async setAyaNeoCustomRgb(config: any): Promise<boolean> {
    return await this.setCustomRgb("ayaneo", config);
  }

  // get_led_capabilities
  // DEPRECATED: Use getDeviceCapabilities().led_capabilities instead
  // 已废弃：请使用 getDeviceCapabilities().led_capabilities
  public static async getLedCapabilities(): Promise<{
    sysfs_single_color: boolean;
    sysfs_multi_zone: boolean;
    ec_access: boolean;
    is_legacy_ec: boolean;
  }> {
    const result = await call("get_led_capabilities");
    return result as any || {
      sysfs_single_color: false,
      sysfs_multi_zone: false,
      ec_access: false,
      is_legacy_ec: false
    };
  }
}
