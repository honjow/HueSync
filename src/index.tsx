import {
  definePlugin,
  PanelSection,
  staticClasses,
} from "@decky/ui";
import { FC } from "react";
import { FaLightbulb } from "react-icons/fa";

import { localizeStrEnum, localizationManager } from "./i18n";
import { RGBComponent, SuspendModeComponent, PowerLedControl, PerAppControl, AcStateControl } from "./components";
import { Backend, RunningApps, ACStateManager } from "./util";
import { Setting } from "./hooks";
import { MoreComponent } from "./components/more";
import { SteamUtils } from "./util/steamUtils";

const Content: FC = () => {

  return (
    <>
      <PanelSection
        title={localizationManager.getString(localizeStrEnum.TITEL_SETTINGS)}
      >
        <PerAppControl />
        <AcStateControl />
        <SuspendModeComponent />
        <PowerLedControl />
      </PanelSection>
      <RGBComponent />
      <MoreComponent />
    </>
  );
};

export default definePlugin(() => {
  const init = async () => {
    await localizationManager.init();
    await Backend.init();
    await Setting.init();

    // Register app and AC state monitoring
    RunningApps.register();
    ACStateManager.register();

    // Listen for app changes
    RunningApps.listenActiveChange((newAppId, oldAppId) => {
      console.log(`[HueSync] App changed: ${oldAppId} -> ${newAppId}`);
      Backend.applySettings({ isInit: false });
      Setting.notifyChange();
    });

    // Listen for AC state changes
    ACStateManager.onACStateChange(() => {
      console.log(`[HueSync] AC state changed`);
      Backend.applySettings({ isInit: false });
      Setting.notifyChange();
    });

    Backend.applySettings({ isInit: true });
  }

  init();

  SteamUtils.RegisterForOnResumeFromSuspend(async () => {
    setTimeout(async () => {
      // Call backend resume first for device-specific handling
      // 先调用后端 resume 处理设备特定逻辑（如 ROG Ally 动态灯光、Legion 电源灯、OneXPlayer 状态缓存）
      await Backend.resume();
      
      // Reapply settings (with init=true for state cache clearing)
      // 重新应用设置（init=true 清除状态缓存）
      Backend.applySettings({ isInit: true });

      console.log("Resume from suspend");
    }, 5000);
  });

  SteamUtils.RegisterForOnSuspendRequest(async () => {
    // Call backend suspend for device-specific handling
    // 调用后端 suspend 处理设备特定逻辑（如电源灯关闭、设备缓存清理）
    await Backend.suspend();

    console.log("Entering suspend mode");
  });
  return {
    title: <div className={staticClasses.Title}>HueSync</div>,
    content: <Content />,
    icon: <FaLightbulb />,
    onDismount() {
      RunningApps.unregister();
      ACStateManager.unregister();
    },
  };
});
