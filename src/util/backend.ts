import { Setting } from "../hooks";
import { call } from "@decky/api";

export class BackendData {
  private current_version = "";
  private latest_version = "";

  public async init() {

    await call<[], string>("get_version").then(
      (result) => {
        console.info("current_version = " + result);
        this.current_version = result;
      }
    );

    await call<[], string>(
      "get_latest_version",
    ).then((result) => {
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

  private static applyRGB(red: number, green: number, blue: number) {
    console.log(`Applying ledOn ${red} ${green} ${blue}`);
    call<[r: number, g: number, b: number], void>("setRGB",
      red,
      green,
      blue,
    );
  }

  private static applyLedOff() {
    console.log("Applying ledOff ");
    call("setOff");
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
