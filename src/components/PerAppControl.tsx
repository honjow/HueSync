import { FC, useEffect, useState } from "react";
import { PanelSectionRow, ToggleField, Marquee } from "@decky/ui";
import { Setting } from "../hooks/settings";
import { RunningApps, DEFAULT_APP } from "../util";
import { localizationManager, localizeStrEnum } from "../i18n";

export const PerAppControl: FC = () => {
  const [override, setOverride] = useState<boolean>(Setting.appOverWrite());
  const [overrideable, setOverrideable] = useState<boolean>(
    RunningApps.active() !== DEFAULT_APP
  );

  useEffect(() => {
    const unregister = RunningApps.listenActiveChange(() => {
      setOverride(Setting.appOverWrite());
      setOverrideable(RunningApps.active() !== DEFAULT_APP);
    });

    return () => {
      unregister();
    };
  }, []);

  if (!overrideable) {
    return null;
  }

  const appInfo = RunningApps.active_appInfo();

  return (
    <PanelSectionRow>
      <ToggleField
        label={localizationManager.getString(
          localizeStrEnum.USE_PERGAME_PROFILE
        )}
        description={
          <div style={{ display: "flex", justifyContent: "left" }}>
            <img
              src={
                appInfo?.icon_data
                  ? "data:image/" +
                    appInfo.icon_data_format +
                    ";base64," +
                    appInfo.icon_data
                  : "/assets/" +
                    appInfo?.appid +
                    "/" +
                    appInfo?.icon_hash +
                    ".jpg?c=" +
                    appInfo?.local_cache_version
              }
              width={20}
              height={20}
              style={{
                marginRight: "5px",
                display: override && overrideable ? "block" : "none",
                borderRadius: "4px",
              }}
            />
            <div style={{ lineHeight: "20px", whiteSpace: "pre" }}>
              {localizationManager.getString(localizeStrEnum.USING) +
                (override && overrideable ? "『" : "")}
            </div>
            {/* @ts-ignore */}
            <Marquee
              play={true}
              fadeLength={10}
              delay={1}
              style={{
                maxWidth: "100px",
                lineHeight: "20px",
                whiteSpace: "pre",
              }}
            >
              {override && overrideable
                ? appInfo?.display_name || ""
                : localizationManager.getString(localizeStrEnum.DEFAULT)}
            </Marquee>
            <div style={{ lineHeight: "20px", whiteSpace: "pre" }}>
              {(override && overrideable ? "』" : "") +
                localizationManager.getString(localizeStrEnum.PROFILE)}
            </div>
          </div>
        }
        checked={override && overrideable}
        disabled={!overrideable}
        onChange={(value) => {
          Setting.setOverWrite(value);
          setOverride(value);
        }}
      />
    </PanelSectionRow>
  );
};

