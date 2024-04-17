import { ServerAPI } from "decky-frontend-lib";
import { Setting } from "../hooks";

export class BackendData {
  private serverAPI: ServerAPI | undefined;
  private current_version = "1.0.0";
  private latest_version = "";

  public async init(serverAPI: ServerAPI) {
    this.serverAPI = serverAPI;

    await this.serverAPI!.callPluginMethod<{}, string>("get_version", {}).then(
      (res) => {
        if (res.success) {
          console.info("current_version = " + res.result);
          this.current_version = res.result;
        }
      }
    );

    await this.serverAPI!.callPluginMethod<{}, string>(
      "get_latest_version",
      {}
    ).then((res) => {
      if (res.success) {
        console.info("latest_version = " + res.result);
        this.latest_version = res.result;
      }
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
  private static serverAPI: ServerAPI;
  public static data: BackendData;

  public static async init(serverAPI: ServerAPI) {
    this.serverAPI = serverAPI;
    this.data = new BackendData();
    await this.data.init(serverAPI);
  }

  private static applyRGB(red: number, green: number, blue: number) {
    console.log(`Applying ledOn ${red} ${green} ${blue}`);
    Backend.serverAPI!.callPluginMethod("setRGB", {
      r: red,
      g: green,
      b: blue,
    });
  }

  private static applyLedOff() {
    console.log("Applying ledOff ");
    Backend.serverAPI!.callPluginMethod("setOff", {});
  }

  public static throwSuspendEvt() {
    if (!Setting.getEnableControl()) {
      return;
    }
    console.log("throwSuspendEvt");
    // this.serverAPI!.callPluginMethod("setOff", {});
  }

  // get_suspend_mode
  public static async getSuspendMode(): Promise<string> {
    return (await this.serverAPI!.callPluginMethod("get_suspend_mode", {}))
      .result as string;
  }

  // set_suspend_mode
  public static async setSuspendMode(mode: string) {
    await this.serverAPI!.callPluginMethod("set_suspend_mode", { mode });
  }

  public static async getLatestVersion(): Promise<string> {
    return (await this.serverAPI!.callPluginMethod("get_latest_version", {}))
      .result as string;
  }

  // updateLatest
  public static async updateLatest() {
    await this.serverAPI!.callPluginMethod("update_latest", {});
  }

  // is_support_suspend_mode
  public static async isSupportSuspendMode(): Promise<boolean> {
    return (await this.serverAPI!.callPluginMethod("is_support_suspend_mode", {}))
      .result as boolean;
  }

  public static applySettings = () => {
    if (!Setting.getEnableControl()) {
      return;
    }

    console.log(`HusSync: set suspend mode ${Setting.getSuspendMode()}`)
    Backend.setSuspendMode(Setting.getSuspendMode());

    if (Setting.getLedOn()) {
      Backend.applyRGB(Setting.getRed(), Setting.getGreen(), Setting.getBlue());
    } else {
      Backend.applyLedOff();
    }
  };
}
