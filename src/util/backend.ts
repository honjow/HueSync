import { Setting, SettingsData } from "../hooks";
import { call } from "@decky/api";
import { debounce } from "lodash";
import { RGBModeCapabilities } from ".";

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

  private static applyColor(
    mode: string,
    red: number,
    green: number,
    blue: number,
    red2: number,
    green2: number,
    blue2: number,
    brightness: number
  ) {
    console.log(
      `Applying color: ${mode} ${red} ${green} ${blue} ${red2} ${green2} ${blue2} ${brightness}`
    );
    call<
      [
        mode: string,
        r: number,
        g: number,
        b: number,
        r2: number,
        g2: number,
        b2: number,
        brightness: number
      ],
      void
    >("set_color", mode, red, green, blue, red2, green2, blue2, brightness);
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

  private static _applySettings = () => {
    if (!Setting.enableControl) {
      return;
    }

    if (Setting.isSupportSuspendMode) {
      console.log(`HueSync: set suspend mode [${Setting.suspendMode}]`);
      Backend.setSuspendMode(Setting.suspendMode);
    }

    Backend.applyColor(
      Setting.mode,
      Setting.red,
      Setting.green,
      Setting.blue,
      Setting.red2,
      Setting.green2,
      Setting.blue2,
      100
    );
  };

  // 使用防抖，延迟 300ms
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
}
