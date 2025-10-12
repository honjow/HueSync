import { Backend, hsvToRgb, Logger, RGBMode, RGBModeCapabilities, RunningApps, ACStateManager, EACState, DEFAULT_APP } from "../util";

export class RgbSetting {
  public enableControl = false;
  public mode = "disabled";
  public hue = 0;
  public saturation = 100;
  public brightness = 100;
  public hue2 = 0;
  public saturation2 = 100;
  public brightness2 = 100;
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
}

export class AppRgbData {
  public overwrite: boolean = false;
  public acStateOverwrite: boolean = false;
  public defaultSetting: RgbSetting = new RgbSetting();
  public acSetting: RgbSetting = new RgbSetting();
  public batSetting: RgbSetting = new RgbSetting();

  public deepCopy(source: AppRgbData) {
    this.overwrite = source.overwrite;
    this.acStateOverwrite = source.acStateOverwrite;
    this.defaultSetting.deepCopy(source.defaultSetting);
    this.acSetting.deepCopy(source.acSetting);
    this.batSetting.deepCopy(source.batSetting);
  }
}

export class SettingsData {
  // Per-App RGB configurations
  public perApp: { [appId: string]: AppRgbData } = {};
  
  // Global settings (not per-app)
  public suspendMode = "";
  public powerLedEnabled = true;
  public powerLedSuspendOff = false;

  public deepCopy(source: SettingsData) {
    this.suspendMode = source.suspendMode;
    this.powerLedEnabled = source.powerLedEnabled;
    this.powerLedSuspendOff = source.powerLedSuspendOff;
    
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
        // Load AC setting
        if (appData.acSetting) {
          Object.assign(this.perApp[appId].acSetting, appData.acSetting);
        }
        // Load battery setting
        if (appData.batSetting) {
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
    
    // Copy to AC and battery settings as well
    defaultApp.acSetting.deepCopy(oldSettings);
    defaultApp.batSetting.deepCopy(oldSettings);
    
    this.perApp = { "0": defaultApp };
  }
}

export class Setting {
  private static _settingsData: SettingsData = new SettingsData();

  // Static members | 静态成员
  public static isSupportSuspendMode: boolean = false;
  public static modeCapabilities: Record<string, RGBModeCapabilities> = {};

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
      
      // Copy from default if exists
      if (DEFAULT_APP in this._settingsData.perApp) {
        this._settingsData.perApp[appId].defaultSetting.deepCopy(
          this._settingsData.perApp[DEFAULT_APP].defaultSetting
        );
        this._settingsData.perApp[appId].acSetting.deepCopy(
          this._settingsData.perApp[DEFAULT_APP].acSetting
        );
        this._settingsData.perApp[appId].batSetting.deepCopy(
          this._settingsData.perApp[DEFAULT_APP].batSetting
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
      return appData.acSetting;
    } else {
      return appData.batSetting;
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
    }
  }

  // AC state override switch
  static appACStateOverWrite(): boolean {
    return this._settingsData.perApp[this.ensureAppID()].acStateOverwrite ?? false;
  }

  static setACStateOverWrite(acStateOverwrite: boolean) {
    if (this.appACStateOverWrite() !== acStateOverwrite) {
      this._settingsData.perApp[this.ensureAppID()].acStateOverwrite = acStateOverwrite;
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  public static async init() {
    await this.loadSettingsData();

    // Ensure DEFAULT_APP exists
    if (!(DEFAULT_APP in this._settingsData.perApp)) {
      this._settingsData.perApp[DEFAULT_APP] = new AppRgbData();
    }

    const [isSupportSuspendMode, modeCapabilities] = await Promise.all([
      Backend.isSupportSuspendMode(),
      Backend.getModeCapabilities(),
    ]);

    this.isSupportSuspendMode = isSupportSuspendMode;
    this.modeCapabilities = modeCapabilities;
  }

  public static async loadSettingsData() {
    const _settingsData = await Backend.getSettings();
    this.settingsData.deepCopy(_settingsData);
  }

  public static async saveSettingsData() {
    Logger.info(`HueSync: saveSettingsData: ${JSON.stringify(this.settingsData)}`);
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
