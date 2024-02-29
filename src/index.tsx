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
import { RGBComponent } from "./components";
import { Backend } from "./util";
import { Setting } from "./hooks";

const Content: VFC = () => {
  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.getEnableControl()
  );

  useEffect(() => {
    Setting.setEnableControl(enableControl);
  }, [enableControl]);

  return (
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
      <RGBComponent />
    </PanelSection>
  );
};

export default definePlugin((serverApi: ServerAPI) => {
  Setting.loadSettingsFromLocalStorage();
  localizationManager.init(serverApi);
  Backend.init(serverApi);
  Backend.applySettings();
  SteamClient.System.RegisterForOnResumeFromSuspend(async () => {
    Backend.applySettings();
    console.log("结束休眠");
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
