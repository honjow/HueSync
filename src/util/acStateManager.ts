export enum EACState {
  Unknown = 0,
  Disconnected = 1,
  Connected = 2,
  Charging = 3,
}

type ACStateChangeHandler = () => void;

export class ACStateManager {
  private static acState: EACState = EACState.Unknown;
  private static acStateListeners: any;
  private static changeHandlers: ACStateChangeHandler[] = [];

  static register() {
    this.acStateListeners = SteamClient.System.RegisterForBatteryStateChanges(
      (batteryStateChange: any) => {
        if (this.acState === batteryStateChange.eACState) {
          return;
        }

        console.log(
          `[HueSync] AC State changed: ${this.acState} -> ${batteryStateChange.eACState}`
        );

        this.acState = batteryStateChange.eACState;
        
        // Notify all registered handlers
        this.changeHandlers.forEach((handler) => {
          try {
            handler();
          } catch (e) {
            console.error("[HueSync] Error in AC state change handler:", e);
          }
        });
      }
    );
  }

  static unregister() {
    this.acStateListeners?.unregister();
    this.changeHandlers = [];
  }

  static getACState(): EACState {
    return this.acState;
  }

  static onACStateChange(handler: ACStateChangeHandler): () => void {
    this.changeHandlers.push(handler);
    return () => {
      const index = this.changeHandlers.indexOf(handler);
      if (index > -1) {
        this.changeHandlers.splice(index, 1);
      }
    };
  }
}

