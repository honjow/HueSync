import { definePlugin, PanelSection, staticClasses } from "@decky/ui";
import { FC } from "react";
import { FaLightbulb } from "react-icons/fa";

import { localizeStrEnum, localizationManager } from "./i18n";
import { RGBComponent, SuspendModeComponent } from "./components";
import { Backend } from "./util";
import { Setting } from "./hooks";
import { MoreComponent } from "./components/more";
import {
  getResumeObservable,
  getSuspendObservable,
} from "./sleep/suspendResumeObservables";

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

const onResume = async () => {
  setTimeout(() => {
    Backend.applySettings({ isInit: true });
    console.log("Resume from suspend");
  }, 5000);
};

const onSuspend = async () => {
  Backend.throwSuspendEvt();
  console.log("Entering suspend mode");
};

export default definePlugin(() => {
  const init = async () => {
    await localizationManager.init();
    await Backend.init();
    await Setting.init();
    Backend.applySettings({ isInit: true });
  };

  init();

  try {
    SteamClient.System.RegisterForOnResumeFromSuspend(onResume);

    SteamClient.System.RegisterForOnSuspendRequest(onSuspend);
  } catch (e) {
    console.error(
      `SteamClient.System suspend/resume hooks no longer available ${e}, fallback to mobx observable`,
    );

    const suspendObservable = getSuspendObservable();
    const resumeObservable = getResumeObservable();

    suspendObservable?.observe_((change) => {
      const { newValue } = change;
      console.log({ info: `mobX suspend triggered with ${newValue}` });
      if (!newValue) {
        return;
      }
      onSuspend();
    });

    resumeObservable?.observe_((change) => {
      const { newValue } = change;
      console.log({ info: `mobX resume triggered with ${newValue}` });
      if (!newValue) {
        return;
      }
      onResume();
    });
  }

  return {
    title: <div className={staticClasses.Title}>HueSync</div>,
    content: <Content />,
    icon: <FaLightbulb />,
    onDismount() {},
  };
});
