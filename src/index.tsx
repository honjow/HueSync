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
      Backend.applySettings({ isInit: true });

      // Power LED resume handling | 电源灯唤醒恢复
      if (Setting.powerLedSuspendOff) {
        const savedState = sessionStorage.getItem('powerLedStateBeforeSuspend');
        if (savedState === 'true') {
          await Backend.setPowerLight(true);
          sessionStorage.removeItem('powerLedStateBeforeSuspend');
          console.log("Power LED restored after resume");
        }
      }

      console.log("Resume from suspend");
    }, 5000);
  });

  SteamUtils.RegisterForOnSuspendRequest(async () => {
    Backend.throwSuspendEvt();

    // Power LED suspend handling | 电源灯睡眠处理
    if (Setting.powerLedSuspendOff) {
      const currentState = await Backend.getPowerLight();
      if (currentState !== null && currentState === true) {
        // Save state to sessionStorage | 保存状态到 sessionStorage
        sessionStorage.setItem('powerLedStateBeforeSuspend', 'true');
        await Backend.setPowerLight(false);
        console.log("Power LED turned off for suspend");
      }
    }

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
