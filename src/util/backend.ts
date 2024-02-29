import { ServerAPI } from "decky-frontend-lib";
import { Setting } from "../hooks";

export class Backend {
  private static serverAPI: ServerAPI;
  public static async init(serverAPI: ServerAPI) {
    this.serverAPI = serverAPI;
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
    this.serverAPI!.callPluginMethod("setOff", {});
  }

  public static applySettings = () => {
    if (!Setting.getEnableControl()) {
      return;
    }

    if (Setting.getLedOn()) {
      Backend.applyRGB(
        Setting.getRed(),
        Setting.getGreen(),
        Setting.getBlue()
      );
    } else {
      Backend.applyLedOff();
    }
  };
}
