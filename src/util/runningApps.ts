import { Router } from "@decky/ui";

type ActiveAppChangedHandler = (newAppId: string, oldAppId: string) => void;
type UnregisterFn = () => void;

export const DEFAULT_APP = "0";

export interface AppOverviewExt {
  appid: string;
  display_name: string;
  icon_data?: string;
  icon_data_format?: string;
  icon_hash?: string;
  local_cache_version?: number;
}

export class RunningApps {
  private static listeners: ActiveAppChangedHandler[] = [];
  private static lastAppId: string = DEFAULT_APP;
  private static intervalId: any;

  private static pollActive() {
    const newApp = RunningApps.active();
    if (this.lastAppId !== newApp) {
      this.listeners?.forEach((h) => h(newApp, this.lastAppId));
    }
    this.lastAppId = newApp;
  }

  static register() {
    if (this.intervalId === undefined) {
      this.intervalId = setInterval(() => this.pollActive(), 100);
    }
  }

  static unregister() {
    if (this.intervalId !== undefined) {
      clearInterval(this.intervalId);
    }
    this.listeners.splice(0, this.listeners.length);
  }

  static listenActiveChange(fn: ActiveAppChangedHandler): UnregisterFn {
    const idx = this.listeners.push(fn) - 1;
    return () => {
      this.listeners.splice(idx, 1);
    };
  }

  static active(): string {
    return Router.MainRunningApp?.appid || DEFAULT_APP;
  }

  static active_appInfo(): AppOverviewExt | null {
    return (Router.MainRunningApp as unknown as AppOverviewExt) || null;
  }
}

