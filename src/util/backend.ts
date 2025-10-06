import { Setting, SettingsData } from "../hooks";
import { call } from "@decky/api";
import { debounce } from "lodash";
import { Logger, RGBModeCapabilities } from ".";

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
  brightness?: number;
  speed?: string;
  brightnessLevel?: string;
}

// Exported callable functions
// export const getVersion = callable<[], string>("get_version");
// export const getLatestVersion = callable<[], string>("get_latest_version");
// export const updateLatest = callable<[], any>("update_latest");

export class BackendData {
  private current_version = "";
  private latest_version = "";

  public async init() {
    await call<[], string>("get_version").then((result) => {
      console.info("current_version = " + result);
      this.current_version = result;
    });

    await call<[], string>("get_latest_version").then((result) => {
      console.info("latest_version = " + result);
      this.latest_version = result;
    });
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
      `Applying color: mode=${options.mode} r=${options.red} g=${options.green} b=${options.blue} r2=${options.red2} g2=${options.green2} b2=${options.blue2} init=${options.isInit} brightness=${options.brightness} speed=${options.speed} brightnessLevel=${options.brightnessLevel}`,
    );
    const {
      mode = "disabled",
      red = 0,
      green = 0,
      blue = 0,
      red2 = 0,
      green2 = 0,
      blue2 = 0,
      isInit = false,
      brightness = 100,
      speed = "low",
      brightnessLevel = "high",
    } = options;
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
      ],
      void
    >("set_color", mode, red, green, blue, red2, green2, blue2, isInit, brightness, speed, brightnessLevel);
  }

  public static throwSuspendEvt() {
    if (!Setting.enableControl) {
      return;
    }
    console.log("throwSuspendEvt");
    // this.serverAPI!.callPluginMethod("setOff", {});
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

  private static _applySettings = ({ isInit = false }: ApplySettingsOptions = {}) => {
    if (!Setting.enableControl) {
      return;
    }

    if (Setting.isSupportSuspendMode) {
      Logger.info(`HueSync: set suspend mode [${Setting.suspendMode}]`);
      Backend.setSuspendMode(Setting.suspendMode);
    }

    Backend.applyColor({
      mode: Setting.mode,
      red: Setting.red,
      green: Setting.green,
      blue: Setting.blue,
      red2: Setting.red2,
      green2: Setting.green2,
      blue2: Setting.blue2,
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

  // get_mode_capabilities
  public static async getModeCapabilities(): Promise<
    Record<string, RGBModeCapabilities>
  > {
    return (await call("get_mode_capabilities")) as Record<
      string,
      RGBModeCapabilities
    >;
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
}
