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
import { SteamUtils } from "./util/steamUtils";

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

  SteamUtils.RegisterForOnResumeFromSuspend(async () => {
    setTimeout(() => {
      Backend.applySettings({ isInit: true });
      console.log("Resume from suspend");
    }, 5000);
  });

  SteamUtils.RegisterForOnSuspendRequest(async () => {
    Backend.throwSuspendEvt();
    console.log("Entering suspend mode");
  });
  return {
    title: <div className={staticClasses.Title}>HueSync</div>,
    content: <Content />,
    icon: <FaLightbulb />,
    onDismount() { },
  };
});
