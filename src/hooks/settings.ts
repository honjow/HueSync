import { Backend, hsvToRgb, RGBMode } from "../util";

export class SettingsData {
  public enableControl = false;
  public mode = "disabled";
  public red = 0;
  public green = 0;
  public blue = 0;
  public hue = 0;
  public saturation = 100;
  public brightness = 100;
  public suspendMode = "";

  public deepCopy(source: SettingsData) {
    this.enableControl = source.enableControl;
    this.mode = source.mode;
    this.red = source.red;
    this.green = source.green;
    this.blue = source.blue;
    this.hue = source.hue;
    this.saturation = source.saturation;
    this.brightness = source.brightness;
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
  private static _instance: Setting = new Setting();

  private _settingsData: SettingsData;

  private constructor() {
    this._settingsData = new SettingsData();
  }

  isSupportSuspendMode: boolean = false;

  public static async init() {
    await this.loadSettingsData();

    Backend.isSupportSuspendMode().then((isSupportSuspendMode) => {
      this._instance.isSupportSuspendMode = isSupportSuspendMode;
    });
  }

  private static get settingsData(): SettingsData {
    return this._instance._settingsData;
  }

  public static async loadSettingsData() {
    const _settingsData = await Backend.getSettings();
    this.settingsData.deepCopy(_settingsData);
  }

  public static async saveSettingsData() {
    await Backend.setSettings(this.settingsData);
  }

  public static get enableControl() {
    return this.settingsData.enableControl;
  }

  public static set enableControl(enableControl: boolean) {
    if (this.settingsData.enableControl != enableControl) {
      this.settingsData.enableControl = enableControl;
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static isSupportSuspendMode() {
    return this._instance.isSupportSuspendMode;
  }

  static setHue(hue: number) {
    if (hue == 360) {
      hue = 0;
    }
    if (this.settingsData.hue != hue) {
      this.settingsData.hue = hue;
      this.initRGB();
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static setSaturation(saturation: number) {
    if (this.settingsData.saturation != saturation) {
      this.settingsData.saturation = saturation;
      this.initRGB();
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static setBrightness(brightness: number) {
    if (this.settingsData.brightness != brightness) {
      this.settingsData.brightness = brightness;
      this.initRGB();
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static setSuspendMode(suspendMode: string) {
    if (this.settingsData.suspendMode != suspendMode) {
      this.settingsData.suspendMode = suspendMode;
      this.saveSettingsData();
      Backend.applySettings();
    }
  }

  static getSuspendMode() {
    return this.settingsData.suspendMode ?? "";
  }

  public static getMode(): RGBMode {
    return this.settingsData.mode as RGBMode || RGBMode.disabled;
  }

  static setMode(mode: RGBMode) {
    if (this.settingsData.mode !== mode) {
      console.log(">>> Updating mode from", this.settingsData.mode, "to", mode);
      this.settingsData.mode = mode;
      this.saveSettingsData();
      Backend.applySettings();
    } else {
      console.log(">>> Mode unchanged, skipping update");
    }
  }

  private static initRGB() {
    const [r, g, b] = hsvToRgb(
      this.settingsData.hue!!,
      this.settingsData.saturation!!,
      this.settingsData.brightness!!
    );
    this.settingsData.red = r;
    this.settingsData.green = g;
    this.settingsData.blue = b;
  }

  static getSaturation() {
    return this.settingsData.saturation!!;
  }

  static getBrightness() {
    return this.settingsData.brightness!!;
  }

  static getRed() {
    return this.settingsData.red!!;
  }

  static getGreen() {
    return this.settingsData.green!!;
  }

  static getBlue() {
    return this.settingsData.blue!!;
  }

  static getHue() {
    return this.settingsData.hue!!;
  }

}
