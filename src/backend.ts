import {ServerAPI } from "decky-frontend-lib";
import { Setting } from "./settings";



export class Backend {
  private static serverAPI: ServerAPI;
  public static async init(serverAPI: ServerAPI) {
    this.serverAPI = serverAPI;
  }

  private static applyLedOn(red: number, green: number, blue: number) {
      console.log(`Applying ledOn ${red} ${green} ${blue}`);
      Backend.serverAPI!.callPluginMethod("set_ledOn", {"r": red, "g": green, "b": blue });
  }

  private static applyLedOff() {
    console.log("Applying ledOff ");
    Backend.serverAPI!.callPluginMethod("set_ledOff", {});
  }

  public static throwSuspendEvt(){
    console.log("throwSuspendEvt");
    this.serverAPI!.callPluginMethod("set_ledOff", {});
  }

  public static applySettings = () => {
    if(Setting.getLedOn()){
      Backend.applyLedOn(Setting.getRed(),Setting.getGreen(),Setting.getBlue());
    }else{
      Backend.applyLedOff();
    }
  };
}
