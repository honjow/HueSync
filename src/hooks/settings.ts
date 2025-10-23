import { Backend, hsvToRgb, RGBMode, RGBModeCapabilities, RunningApps, ACStateManager, EACState, DEFAULT_APP, DeviceCapabilities } from "../util";

export class RgbSetting {
  public enableControl = false;
  public mode = "disabled";
  public hue = 0;
  public saturation = 100;
  public brightness = 100;
  public hue2 = 0;
  public saturation2 = 100;
  public brightness2 = 100;
  public secondaryZoneHue = 0;
  public secondaryZoneSaturation = 100;
  public secondaryZoneBrightness = 100;
  public secondaryZoneEnabled = true;  // Default to enabled for backward compatibility
  public speed = "low";
  public brightnessLevel = "high";

  public deepCopy(source: RgbSetting) {
    this.enableControl = source.enableControl;
    this.mode = source.mode;
    this.hue = source.hue;
    this.saturation = source.saturation;
    this.brightness = source.brightness;
    this.hue2 = source.hue2;
    this.saturation2 = source.saturation2;
    this.brightness2 = source.brightness2;
    this.secondaryZoneHue = source.secondaryZoneHue;
    this.secondaryZoneSaturation = source.secondaryZoneSaturation;
    this.secondaryZoneBrightness = source.secondaryZoneBrightness;
    this.secondaryZoneEnabled = source.secondaryZoneEnabled;
    this.speed = source.speed;
    this.brightnessLevel = source.brightnessLevel;
  }

  // RGB getters
  get red(): number {
    const [r] = hsvToRgb(this.hue, this.saturation, this.brightness);
    return r;
  }

  get green(): number {
    const [, g] = hsvToRgb(this.hue, this.saturation, this.brightness);
    return g;
  }

  get blue(): number {
    const [, , b] = hsvToRgb(this.hue, this.saturation, this.brightness);
    return b;
  }

  get red2(): number {
    const [r] = hsvToRgb(this.hue2, this.saturation2, this.brightness2);
    return r;
  }

  get green2(): number {
    const [, g] = hsvToRgb(this.hue2, this.saturation2, this.brightness2);
    return g;
  }

  get blue2(): number {
    const [, , b] = hsvToRgb(this.hue2, this.saturation2, this.brightness2);
    return b;
  }

  get secondaryZoneRed(): number {
    const [r] = hsvToRgb(this.secondaryZoneHue, this.secondaryZoneSaturation, this.secondaryZoneBrightness);
    return r;
  }

  get secondaryZoneGreen(): number {
    const [, g] = hsvToRgb(this.secondaryZoneHue, this.secondaryZoneSaturation, this.secondaryZoneBrightness);
    return g;
  }

  get secondaryZoneBlue(): number {
    const [, , b] = hsvToRgb(this.secondaryZoneHue, this.secondaryZoneSaturation, this.secondaryZoneBrightness);
    return b;
  }
}

export class AppRgbData {
  public overwrite: boolean = false;
  public acStateOverwrite: boolean = false;
  public defaultSetting: RgbSetting = new RgbSetting();
  public acSetting: RgbSetting | null = null;
  public batSetting: RgbSetting | null = null;

  public deepCopy(source: AppRgbData) {
    this.overwrite = source.overwrite;
    this.acStateOverwrite = source.acStateOverwrite;
    this.defaultSetting.deepCopy(source.defaultSetting);
    
    if (source.acSetting !== null) {
      this.acSetting = new RgbSetting();
      this.acSetting.deepCopy(source.acSetting);
    } else {
      this.acSetting = null;
    }
    
    if (source.batSetting !== null) {
      this.batSetting = new RgbSetting();
      this.batSetting.deepCopy(source.batSetting);
    } else {
      this.batSetting = null;
    }
  }
}

export class SettingsData {
  // Per-App RGB configurations
  public perApp: { [appId: string]: AppRgbData } = {};
  
  // Global settings (not per-app)
  public suspendMode = "";
  public powerLedEnabled = true;
  public powerLedSuspendOff = false;
  
  // MSI Custom RGB - currently applied preset name
  public currentMsiCustomPreset: string | null = null;

  public deepCopy(source: SettingsData) {
    this.suspendMode = source.suspendMode;
    this.powerLedEnabled = source.powerLedEnabled;
    this.powerLedSuspendOff = source.powerLedSuspendOff;
    this.currentMsiCustomPreset = source.currentMsiCustomPreset;
    
    this.perApp = {};
    Object.entries(source.perApp).forEach(([key, value]) => {
      this.perApp[key] = new AppRgbData();
      this.perApp[key].deepCopy(value);
    });
  }

  public fromDict(dict: { [key: string]: any }) {
    console.log(`SettingsData.fromDict: ${JSON.stringify(dict)}`);
    
    // Handle global settings
    if (dict.suspendMode !== undefined) {
      this.suspendMode = dict.suspendMode;
    }
    if (dict.powerLedEnabled !== undefined) {
      this.powerLedEnabled = dict.powerLedEnabled;
    }
    if (dict.powerLedSuspendOff !== undefined) {
      this.powerLedSuspendOff = dict.powerLedSuspendOff;
    }
    if (dict.currentMsiCustomPreset !== undefined) {
      this.currentMsiCustomPreset = dict.currentMsiCustomPreset;
    }
    
    // Handle per-app settings
    if (dict.perApp !== undefined) {
      this.perApp = {};
      Object.entries(dict.perApp).forEach(([appId, appData]: [string, any]) => {
        this.perApp[appId] = new AppRgbData();
        if (appData.overwrite !== undefined) {
          this.perApp[appId].overwrite = appData.overwrite;
        }
        if (appData.acStateOverwrite !== undefined) {
          this.perApp[appId].acStateOverwrite = appData.acStateOverwrite;
        }
        
        // Load default setting
        if (appData.defaultSetting) {
          Object.assign(this.perApp[appId].defaultSetting, appData.defaultSetting);
        }
        // Load AC setting (only if exists in saved data)
        if (appData.acSetting) {
          this.perApp[appId].acSetting = new RgbSetting();
          Object.assign(this.perApp[appId].acSetting, appData.acSetting);
        }
        // Load battery setting (only if exists in saved data)
        if (appData.batSetting) {
          this.perApp[appId].batSetting = new RgbSetting();
          Object.assign(this.perApp[appId].batSetting, appData.batSetting);
        }
      });
    } else {
      // Migration: Convert old format to new per-app format
      this.migrateFromOldFormat(dict);
    }
  }

  private migrateFromOldFormat(dict: { [key: string]: any }) {
    // Create default app entry with old settings
    const defaultApp = new AppRgbData();
    defaultApp.overwrite = false;
    defaultApp.acStateOverwrite = false;
    
    const oldSettings = defaultApp.defaultSetting;
    if (dict.enableControl !== undefined) oldSettings.enableControl = dict.enableControl;
    if (dict.mode !== undefined) oldSettings.mode = dict.mode;
    if (dict.hue !== undefined) oldSettings.hue = dict.hue;
    if (dict.saturation !== undefined) oldSettings.saturation = dict.saturation;
    if (dict.brightness !== undefined) oldSettings.brightness = dict.brightness;
    if (dict.hue2 !== undefined) oldSettings.hue2 = dict.hue2;
    if (dict.saturation2 !== undefined) oldSettings.saturation2 = dict.saturation2;
    if (dict.brightness2 !== undefined) oldSettings.brightness2 = dict.brightness2;
    if (dict.speed !== undefined) oldSettings.speed = dict.speed;
    if (dict.brightnessLevel !== undefined) oldSettings.brightnessLevel = dict.brightnessLevel;
    
    // For old format migration, keep AC and battery settings as copies of default
    // This preserves the old behavior for existing users
    defaultApp.acSetting = new RgbSetting();
    defaultApp.acSetting.deepCopy(oldSettings);
    defaultApp.batSetting = new RgbSetting();
    defaultApp.batSetting.deepCopy(oldSettings);
    
    this.perApp = { "0": defaultApp };
  }
}

export class Setting {
  private static _settingsData: SettingsData = new SettingsData();

  // Static members | 静态成员
  public static isSupportSuspendMode: boolean = false;
  public static modeCapabilities: Record<string, RGBModeCapabilities> = {};
  public static deviceCapabilities: DeviceCapabilities | null = null;
  
  // MSI Custom RGB - currently applied preset name
  // MSI 自定义 RGB - 当前应用的预设名称
  public static currentMsiCustomPreset: string | null = null;

  // Event system for configuration changes | 配置变更事件系统
  private static settingChangeEvent = new EventTarget();

  private constructor() {}

  private static get settingsData(): SettingsData {
    return this._settingsData;
  }

  // ========== Event System Methods ==========

  // Register a listener for configuration changes | 注册配置变更监听器
  static onSettingChange(callback: () => void): () => void {
    const handler = () => callback();
    this.settingChangeEvent.addEventListener("change", handler);
    return () => {
      this.settingChangeEvent.removeEventListener("change", handler);
    };
  }

  // Notify all listeners that configuration has changed | 通知所有监听器配置已变更
  static notifyChange() {
    this.settingChangeEvent.dispatchEvent(new Event("change"));
  }

  // ========== Per-App Configuration Methods ==========

  // Get current app ID (default or current)
  private static ensureAppID(): string {
    const appId = RunningApps.active();
    
    // Ensure app entry exists
    if (!(appId in this._settingsData.perApp)) {
      this._settingsData.perApp[appId] = new AppRgbData();
      
      // Copy only defaultSetting from DEFAULT_APP if exists
      // acSetting and batSetting remain null until user enables acStateOverwrite
      if (DEFAULT_APP in this._settingsData.perApp) {
        this._settingsData.perApp[appId].defaultSetting.deepCopy(
          this._settingsData.perApp[DEFAULT_APP].defaultSetting
        );
      }
    }
    
    return this._settingsData.perApp[appId]?.overwrite ? appId : DEFAULT_APP;
  }

  // Get current RGB setting based on app and AC state
  private static ensureRgbSetting(): RgbSetting {
    const appId = this.ensureAppID();
    
    if (!(appId in this._settingsData.perApp)) {
      this._settingsData.perApp[appId] = new AppRgbData();
    }
    
    const appData = this._settingsData.perApp[appId];
    
    // If AC state override is not enabled, use default setting
    if (!appData.acStateOverwrite) {
      return appData.defaultSetting;
    }
    
    // Return setting based on AC state
    if (ACStateManager.getACState() === EACState.Connected) {
      // If acSetting is null (never configured), fallback to defaultSetting
      return appData.acSetting !== null ? appData.acSetting : appData.defaultSetting;
    } else {
      // If batSetting is null (never configured), fallback to defaultSetting
      return appData.batSetting !== null ? appData.batSetting : appData.defaultSetting;
    }
  }

  // App override switch
  static appOverWrite(): boolean {
    const appId = RunningApps.active();
    if (appId === DEFAULT_APP) {
      return false;
    }
    return this._settingsData.perApp[appId]?.overwrite ?? false;
  }

  static setOverWrite(overwrite: boolean) {
    const appId = RunningApps.active();
    if (appId !== DEFAULT_APP && this.appOverWrite() !== overwrite) {
      this._settingsData.perApp[appId].overwrite = overwrite;
      this.saveSettingsData();
      Backend.applySettings();
      this.notifyChange();
    }
  }

  // AC state override switch
  static appACStateOverWrite(): boolean {
    return this._settingsData.perApp[this.ensureAppID()].acStateOverwrite ?? false;
  }

  static setACStateOverWrite(acStateOverwrite: boolean) {
    if (this.appACStateOverWrite() !== acStateOverwrite) {
      const appId = this.ensureAppID();
      const appData = this._settingsData.perApp[appId];
      
      // When enabling acStateOverwrite for the first time, copy from defaultSetting if null
      if (acStateOverwrite) {
        if (appData.acSetting === null) {
          appData.acSetting = new RgbSetting();
          appData.acSetting.deepCopy(appData.defaultSetting);
        }
        if (appData.batSetting === null) {
          appData.batSetting = new RgbSetting();
          appData.batSetting.deepCopy(appData.defaultSetting);
        }
      }
      
      appData.acStateOverwrite = acStateOverwrite;
      this.saveSettingsData();
      Backend.applySettings();
      this.notifyChange();
    }
  }

  public static async init() {
    await this.loadSettingsData();

    // Ensure DEFAULT_APP exists
    if (!(DEFAULT_APP in this._settingsData.perApp)) {
      this._settingsData.perApp[DEFAULT_APP] = new AppRgbData();
    }

    const [isSupportSuspendMode, modeCapabilities, deviceCapabilities] = await Promise.all([
      Backend.isSupportSuspendMode(),
      Backend.getModeCapabilities(),
      Backend.getDeviceCapabilities(),
    ]);

    this.isSupportSuspendMode = isSupportSuspendMode;
    this.modeCapabilities = modeCapabilities;
    this.deviceCapabilities = deviceCapabilities;
  }

  public static async loadSettingsData() {
    const _settingsData = await Backend.getSettings();
    this.settingsData.deepCopy(_settingsData);
    // Sync currentMsiCustomPreset to static property
    this.currentMsiCustomPreset = this.settingsData.currentMsiCustomPreset;
  }

  public static async saveSettingsData() {
    // Sync static property to settingsData before saving
    this.settingsData.currentMsiCustomPreset = this.currentMsiCustomPreset;
    // Logger.debug(`HueSync: saveSettingsData: ${JSON.stringify(this.settingsData)}`);
    await Backend.setSettings(this.settingsData);
  }

  private static createGetter<T>(
    key: keyof RgbSetting,
    defaultValueFn?: () => T
  ): () => T {
    return () => {
      const setting = this.ensureRgbSetting();
      const value = setting[key] as T;
      return defaultValueFn && value === undefined ? defaultValueFn() : value;
    };
  }

  private static createSetter<T>(
    key: keyof RgbSetting,
    preProcess?: (value: T) => T,
    postProcess?: (oldValue: T, newValue: T) => void
  ): (value: T) => void {
    return (value: T) => {
      const setting = this.ensureRgbSetting();
      const processedValue = preProcess ? preProcess(value) : value;
      if (setting[key] !== processedValue) {
        (setting[key] as T) = processedValue;
        postProcess?.(setting[key] as T, processedValue);
        this.saveSettingsData();
        Backend.applySettings();
      }
    };
  }

  private static settingProperty<T>(
    key: keyof RgbSetting,
    preProcess?: (value: T) => T,
    postProcess?: (oldValue: T, newValue: T) => void
  ) {
    const getter = Setting.createGetter<T>(key);
    const setter = Setting.createSetter<T>(key, preProcess, postProcess);

    return function (target: any, propertyKey: string) {
      Object.defineProperty(target, propertyKey, {
        get: getter,
        set: setter,
        enumerable: true,
        configurable: true,
      });
    };
  }

  private static readonlyProperty<T>(key: keyof RgbSetting) {
    const getter = Setting.createGetter<T>(key);

    return function (target: any, propertyKey: string) {
      Object.defineProperty(target, propertyKey, {
        get: getter,
        enumerable: true,
        configurable: true,
      });
    };
  }

  @Setting.settingProperty<number>("hue")
  public static hue: number;

  @Setting.settingProperty<number>("hue2")
  public static hue2: number;

  @Setting.settingProperty<number>("saturation")
  public static saturation: number;

  @Setting.settingProperty<number>("brightness")
  public static brightness: number;

  @Setting.settingProperty<number>("saturation2")
  public static saturation2: number;

  @Setting.settingProperty<number>("brightness2")
  public static brightness2: number;

  @Setting.settingProperty<RGBMode>("mode")
  public static mode: RGBMode;

  @Setting.settingProperty<boolean>("enableControl")
  public static enableControl: boolean;

  @Setting.readonlyProperty<number>("red")
  public static red: number;

  @Setting.readonlyProperty<number>("green")
  public static green: number;

  @Setting.readonlyProperty<number>("blue")
  public static blue: number;

  @Setting.readonlyProperty<number>("red2")
  public static red2: number;

  @Setting.readonlyProperty<number>("green2")
  public static green2: number;

  @Setting.readonlyProperty<number>("blue2")
  public static blue2: number;

  @Setting.settingProperty<number>("secondaryZoneHue")
  public static secondaryZoneHue: number;

  @Setting.settingProperty<number>("secondaryZoneSaturation")
  public static secondaryZoneSaturation: number;

  @Setting.settingProperty<number>("secondaryZoneBrightness")
  public static secondaryZoneBrightness: number;

  @Setting.readonlyProperty<number>("secondaryZoneRed")
  public static secondaryZoneRed: number;

  @Setting.readonlyProperty<number>("secondaryZoneGreen")
  public static secondaryZoneGreen: number;

  @Setting.readonlyProperty<number>("secondaryZoneBlue")
  public static secondaryZoneBlue: number;

  @Setting.settingProperty<boolean>("secondaryZoneEnabled")
  public static secondaryZoneEnabled: boolean;

  @Setting.settingProperty<string>("speed")
  public static speed: string;

  @Setting.settingProperty<string>("brightnessLevel")
  public static brightnessLevel: string;

  // Global settings (not per-app)
  static get suspendMode(): string {
    return this._settingsData.suspendMode;
  }

  static set suspendMode(value: string) {
    if (this._settingsData.suspendMode !== value) {
      this._settingsData.suspendMode = value;
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static get powerLedEnabled(): boolean {
    return this._settingsData.powerLedEnabled;
  }

  static set powerLedEnabled(value: boolean) {
    if (this._settingsData.powerLedEnabled !== value) {
      this._settingsData.powerLedEnabled = value;
      this.saveSettingsData();
    }
  }

  static get powerLedSuspendOff(): boolean {
    return this._settingsData.powerLedSuspendOff;
  }

  static set powerLedSuspendOff(value: boolean) {
    if (this._settingsData.powerLedSuspendOff !== value) {
      this._settingsData.powerLedSuspendOff = value;
      this.saveSettingsData();
    }
  }
}
