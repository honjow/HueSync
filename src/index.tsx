import {
  definePlugin,
  PanelSection,
  staticClasses,
} from "@decky/ui";
import { FC } from "react";
import { FaLightbulb } from "react-icons/fa";

import { localizeStrEnum, localizationManager } from "./i18n";
import { RGBComponent, SuspendModeComponent } from "./components";
import { Backend } from "./util";
import { Setting } from "./hooks";
import { MoreComponent } from "./components/more";

const Content: FC = () => {

  return (
    <div>
      <PanelSection
        title={localizationManager.getString(localizeStrEnum.TITEL_SETTINGS)}
      >
        <RGBComponent />
        <SuspendModeComponent />
      </PanelSection>
      <MoreComponent />
    </div>
  );
};

export default definePlugin(() => {
  const init = async () => {
    await localizationManager.init();
    await Backend.init();
    await Setting.init();
    Backend.applySettings({ isInit: true });
  }

  init();

  SteamClient.System.RegisterForOnResumeFromSuspend(async () => {
    setTimeout(() => {
      Backend.applySettings({ isInit: true });
      console.log("结束休眠");
    }, 5000);
  });

  SteamClient.System.RegisterForOnSuspendRequest(async () => {
    Backend.throwSuspendEvt();
    console.log("开始休眠");
  });
  return {
    title: <div className={staticClasses.Title}>HueSync</div>,
    content: <Content />,
    icon: <FaLightbulb />,
    onDismount() { },
  };
});
