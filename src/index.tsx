import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses,
  ToggleField,
} from "decky-frontend-lib";
import { VFC, useState, useEffect } from "react";
import { FaLightbulb } from "react-icons/fa";

import { localizeStrEnum, localizationManager } from "./i18n";
import { RGBComponent, SuspendModeComponent } from "./components";
import { Backend } from "./util";
import { Setting } from "./hooks";
import { MoreComponent } from "./components/more";

const Content: VFC = () => {
  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.getEnableControl()
  );

  useEffect(() => {
    Setting.setEnableControl(enableControl);
  }, [enableControl]);

  return (
    <div>
      <PanelSection
        title={localizationManager.getString(localizeStrEnum.TITEL_SETTINGS)}
      >
        <PanelSectionRow>
          <ToggleField
            label={localizationManager.getString(
              localizeStrEnum.ENABLE_LED_CONTROL
            )}
            checked={enableControl}
            onChange={(value) => {
              setEnableControl(value);
            }}
          />
        </PanelSectionRow>
        {enableControl && <RGBComponent />}
        <SuspendModeComponent />
      </PanelSection>
      <MoreComponent />
    </div>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  const init = async () => {
    Setting.loadSettingsFromLocalStorage();
    localizationManager.init();
    Backend.init(serverApi);
    await Setting.init();
    Backend.applySettings();
  }

  init();

  SteamClient.System.RegisterForOnResumeFromSuspend(async () => {
    setTimeout(() => {
      Backend.applySettings();
      console.log("结束休眠");
    }, 3000);
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
