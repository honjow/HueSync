import {
  JsonObject,
  JsonProperty,
  JsonSerializer,
} from "typescript-json-serializer";
import { Backend, hsvToRgb } from "../util";

const SETTINGS_KEY = "HueSync";
const serializer = new JsonSerializer();

@JsonObject()
// @ts-ignore
export class Setting {
  private static _instance: Setting = new Setting();
  @JsonProperty()
  // @ts-ignore
  enableControl?: boolean;
  @JsonProperty()
  // @ts-ignore
  ledOn?: boolean;
  @JsonProperty()
  // @ts-ignore
  red?: number;
  @JsonProperty()
  // @ts-ignore
  green?: number;
  @JsonProperty()
  // @ts-ignore
  blue?: number;
  @JsonProperty()
  // @ts-ignore
  brightness?: number;
  @JsonProperty()
  // @ts-ignore
  hue?: number;
  @JsonProperty()
  // @ts-ignore
  saturation?: number;

  constructor() {
    this.enableControl = false;
    this.ledOn = true;
    this.red = 255;
    this.green = 255;
    this.blue = 255;
    this.hue = 0;
    this.saturation = 100;
    this.brightness = 100;
  }

  static getEnableControl() {
    return this._instance.enableControl!!;
  }

  static setEnableControl(enableControl: boolean) {
    if (this._instance.enableControl != enableControl) {
      this._instance.enableControl = enableControl;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static getLedOn() {
    return this._instance.ledOn!!;
  }

  static setOff() {
    if (this._instance.ledOn != false) {
      this._instance.ledOn = false;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static toggleLed(enable: boolean) {
    if (this._instance.ledOn != enable) {
      this._instance.ledOn = enable;
      this.initRGB();
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  // static applyRGB(red: number, green: number, blue: number) {
  //   if (this._instance.ledOn != true) {
  //     this._instance.ledOn = true;
  //     this._instance.red = red;
  //     this._instance.blue = blue;
  //     this._instance.green = green;
  //     Setting.saveSettingsToLocalStorage();
  //     Backend.applySettings();
  //   }
  // }

  static setHue(hue: number) {
    if (hue == 360) {
      hue = 0;
    }
    if (this._instance.hue != hue) {
      this._instance.hue = hue;
      this.initRGB();
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setSaturation(saturation: number) {
    if (this._instance.saturation != saturation) {
      this._instance.saturation = saturation;
      this.initRGB();
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setBrightness(brightness: number) {
    if (this._instance.brightness != brightness) {
      this._instance.brightness = brightness;
      this.initRGB();
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  private static initRGB() {
    const [r, g, b] = hsvToRgb(
      this._instance.hue!!,
      this._instance.saturation!!,
      this._instance.brightness!!
    );
    this._instance.red = r;
    this._instance.green = g;
    this._instance.blue = b;
  }

  static getSaturation() {
    return this._instance.saturation!!;
  }

  static getBrightness() {
    return this._instance.brightness!!;
  }

  static getRed() {
    return this._instance.red!!;
  }

  static getGreen() {
    return this._instance.green!!;
  }

  static getBlue() {
    return this._instance.blue!!;
  }

  static getHue() {
    return this._instance.hue!!;
  }

  static loadSettingsFromLocalStorage() {
    const settingsString = localStorage.getItem(SETTINGS_KEY) || "{}";
    const settingsJson = JSON.parse(settingsString);
    const loadSetting = serializer.deserializeObject(settingsJson, Setting);
    this._instance = loadSetting ? loadSetting : new Setting();
  }

  static saveSettingsToLocalStorage() {
    const settingsJson = serializer.serializeObject(this._instance);
    const settingsString = JSON.stringify(settingsJson);
    localStorage.setItem(SETTINGS_KEY, settingsString);
  }
}
