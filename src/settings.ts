import {
  JsonObject,
  JsonProperty,
  JsonSerializer,
} from "typescript-json-serializer";
import { Backend } from "./backend";

const SETTINGS_KEY = "AyaLed";
const serializer = new JsonSerializer();

@JsonObject()
// @ts-ignore
export class Setting {
  private static _instance: Setting = new Setting();
  @JsonProperty()
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
  brightness?: number;
  constructor() {
    this.enableControl = false;
    this.ledOn = true;
    this.red = 255;
    this.green = 255;
    this.blue = 255;
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

  static setLedOn(red: number, green: number, blue: number, brightness: number) {
    if (this._instance.ledOn != true) {
      this._instance.ledOn = true;
      this._instance.red = red;
      this._instance.blue = blue;
      this._instance.green = green;
      this._instance.brightness = brightness;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setOff() {
    if (this._instance.ledOn != false) {
      this._instance.ledOn = false;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setRed(red: number) {
    if (this._instance.red != red) {
      this._instance.red = red;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setGreen(green: number) {
    if (this._instance.green != green) {
      this._instance.green = green;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setBlue(blue: number) {
    if (this._instance.blue != blue) {
      this._instance.blue = blue;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
  }

  static setBrightness(brightness: number) {
    if (this._instance.brightness != brightness) {
      this._instance.brightness = brightness;
      Setting.saveSettingsToLocalStorage();
      Backend.applySettings();
    }
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
