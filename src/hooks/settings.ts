import { Backend, hsvToRgb, RGBMode, RGBModeCapabilities } from "../util";

export class SettingsData {
  public enableControl = false;
  public mode = "disabled";
  public hue = 0;
  public saturation = 100;
  public brightness = 100;
  public hue2 = 0;
  public saturation2 = 100;
  public brightness2 = 100;
  public suspendMode = "";

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

  public deepCopy(source: SettingsData) {
    this.enableControl = source.enableControl;
    this.mode = source.mode;
    this.hue = source.hue;
    this.saturation = source.saturation;
    this.brightness = source.brightness;
    this.hue2 = source.hue2;
    this.saturation2 = source.saturation2;
    this.brightness2 = source.brightness2;
    this.suspendMode = source.suspendMode;
  }

  public fromDict(dict: { [key: string]: any }) {
    console.log(`SettingsData.fromDict: ${JSON.stringify(dict)}`);
    for (const key of Object.keys(dict)) {
      if (this.hasOwnProperty(key)) {
        const typedKey = key as keyof SettingsData;
        // 确保类型安全的赋值
        const value = dict[key];
        if (typeof value === typeof this[typedKey]) {
          (this[typedKey] as any) = value;
        }
      }
    }
  }
}

export class Setting {
  private static _settingsData: SettingsData = new SettingsData();

  // 静态成员
  public static isSupportSuspendMode: boolean = false;
  public static modeCapabilities: Record<string, RGBModeCapabilities> = {};

  private constructor() {}

  private static get settingsData(): SettingsData {
    return this._settingsData;
  }

  public static async init() {
    await this.loadSettingsData();

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
    await Backend.setSettings(this.settingsData);
  }

  private static createGetter<T>(
    key: keyof SettingsData,
    defaultValueFn?: () => T
  ): () => T {
    return () => {
      const value = this.settingsData[key] as T;
      return defaultValueFn && value === undefined ? defaultValueFn() : value;
    };
  }

  private static createSetter<T>(
    key: keyof SettingsData,
    preProcess?: (value: T) => T,
    postProcess?: (oldValue: T, newValue: T) => void
  ): (value: T) => void {
    return (value: T) => {
      const processedValue = preProcess ? preProcess(value) : value;
      if (this.settingsData[key] !== processedValue) {
        (this.settingsData[key] as T) = processedValue;
        postProcess?.(this.settingsData[key] as T, processedValue);
        this.saveSettingsData();
        Backend.applySettings();
      }
    };
  }

  private static settingProperty<T>(
    key: keyof SettingsData,
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

  private static readonlyProperty<T>(key: keyof SettingsData) {
    const getter = Setting.createGetter<T>(key);

    return function (target: any, propertyKey: string) {
      Object.defineProperty(target, propertyKey, {
        get: getter,
        enumerable: true,
        configurable: true,
      });
    };
  }

  @Setting.settingProperty<number>("hue", (hue) => (hue === 360 ? 0 : hue))
  public static hue: number;

  @Setting.settingProperty<number>("saturation")
  public static saturation: number;

  @Setting.settingProperty<number>("brightness")
  public static brightness: number;

  @Setting.settingProperty<number>("hue2", (hue) => (hue === 360 ? 0 : hue))
  public static hue2: number;

  @Setting.settingProperty<number>("saturation2")
  public static saturation2: number;

  @Setting.settingProperty<number>("brightness2")
  public static brightness2: number;

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

  @Setting.settingProperty<string>("suspendMode")
  public static suspendMode: string;

  @Setting.settingProperty<RGBMode>("mode", undefined, (oldValue, newValue) => {
    console.log(">>> Updating mode from", oldValue, "to", newValue);
  })
  public static mode: RGBMode;

  @Setting.settingProperty<boolean>("enableControl")
  public static enableControl: boolean;
}
