import {
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ButtonItem,
  staticClasses,
} from "@decky/ui";
import { FC, useEffect, useState } from "react";
import { FaLightbulb } from "react-icons/fa";

import { localizeStrEnum, localizationManager } from "./i18n";
import { RGBComponent, SuspendModeComponent, PowerLedControl, PerAppControl, AcStateControl } from "./components";
import { Backend, RunningApps, ACStateManager } from "./util";
import { Setting } from "./hooks";
import { MoreComponent } from "./components/more";
import { SteamUtils } from "./util/steamUtils";

const Content: FC<{ initialize: () => Promise<void> }> = ({ initialize }) => {
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let mounted = true;
    initialize().then(
      () => {
        if (mounted) setStatus("ready");
      },
      (error) => {
        console.error("[HueSync] Initialization failed", error);
        if (mounted) setStatus("error");
      },
    );
    return () => {
      mounted = false;
    };
  }, [initialize, attempt]);

  if (status !== "ready") {
    return (
      <PanelSection title="HueSync">
        <PanelSectionRow>
          <div role={status === "error" ? "alert" : "status"}>
            {status === "error"
              ? localizationManager.getString(localizeStrEnum.INITIALIZATION_ERROR, {
                  defaultValue: "Could not load device settings. Please retry.",
                })
              : localizationManager.getString(localizeStrEnum.INITIALIZATION_LOADING, {
                  defaultValue: "Loading device settings...",
                })}
          </div>
        </PanelSectionRow>
        {status === "error" && (
          <PanelSectionRow>
            <ButtonItem
              layout="below"
              onClick={() => {
                setStatus("loading");
                setAttempt((value) => value + 1);
              }}
            >
              {localizationManager.getString(localizeStrEnum.INITIALIZATION_RETRY, {
                defaultValue: "Retry",
              })}
            </ButtonItem>
          </PanelSectionRow>
        )}
      </PanelSection>
    );
  }

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
  let disposed = false;
  let initialization: Promise<void> | undefined;
  let ready = false;
  const assertActive = () => {
    if (disposed) throw new Error("HueSync has been unloaded");
  };
  const initialize = (): Promise<void> => {
    if (initialization) return initialization;
    initialization = (async () => {
      assertActive();
      await localizationManager.init();
      assertActive();
      await Setting.init();
      assertActive();

      // Register only after essential settings and capabilities are ready.
      // A failed attempt rolls back registrations before it can be retried.
      try {
        RunningApps.register();
        ACStateManager.register();
        RunningApps.listenActiveChange((newAppId, oldAppId) => {
          console.log(`[HueSync] App changed: ${oldAppId} -> ${newAppId}`);
          Backend.applySettings({ isInit: false });
          Setting.notifyChange();
        });
        ACStateManager.onACStateChange(() => {
          console.log("[HueSync] AC state changed");
          Backend.applySettings({ isInit: false });
          Setting.notifyChange();
        });
        Backend.applySettings({ isInit: true });
      } catch (error) {
        RunningApps.unregister();
        ACStateManager.unregister();
        throw error;
      }
      ready = true;
      // Version checks are optional and must never block the controls.
      void Backend.init().catch((error) => {
        console.error("[HueSync] Version check failed", error);
      });
    })().catch((error) => {
      initialization = undefined;
      throw error;
    });
    return initialization;
  };

  // Start immediately, even while the panel is closed. Attach a rejection
  // handler now; Content presents the error and can start a fresh attempt.
  void initialize().catch((error) => {
    console.error("[HueSync] Initialization failed", error);
  });

  let resumeTimer: ReturnType<typeof setTimeout> | undefined;
  const resumeSubscription = SteamUtils.RegisterForOnResumeFromSuspend(async () => {
    if (disposed || !ready) return;
    clearTimeout(resumeTimer);
    resumeTimer = setTimeout(async () => {
      if (disposed || !ready) return;
      // Call backend resume first for device-specific handling
      // 先调用后端 resume 处理设备特定逻辑（如 ROG Ally 动态灯光、Legion 电源灯、OneXPlayer 状态缓存）
      await Backend.resume();
      if (disposed) return;
      
      // Reapply settings (with init=true for state cache clearing)
      // 重新应用设置（init=true 清除状态缓存）
      Backend.applySettings({ isInit: true });

      console.log("Resume from suspend");
    }, 5000);
  });

  const suspendSubscription = SteamUtils.RegisterForOnSuspendRequest(async () => {
    if (disposed || !ready) return;
    // Call backend suspend for device-specific handling
    // 调用后端 suspend 处理设备特定逻辑（如电源灯关闭、设备缓存清理）
    await Backend.suspend();

    console.log("Entering suspend mode");
  });
  return {
    title: <div className={staticClasses.Title}>HueSync</div>,
    content: <Content initialize={initialize} />,
    icon: <FaLightbulb />,
    onDismount() {
      disposed = true;
      ready = false;
      clearTimeout(resumeTimer);
      resumeSubscription?.unregister();
      suspendSubscription?.unregister();
      Backend.applySettings.cancel();
      RunningApps.unregister();
      ACStateManager.unregister();
    },
  };
});
