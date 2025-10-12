import { FC, useEffect, useState } from "react";
import { PanelSectionRow, ToggleField } from "@decky/ui";
import { Setting } from "../hooks/settings";
import { ACStateManager, EACState } from "../util";
import { localizationManager, localizeStrEnum } from "../i18n";

export const AcStateControl: FC = () => {
  const [acStateOverwrite, setAcStateOverwrite] = useState<boolean>(
    Setting.appACStateOverWrite()
  );
  const [acState, setAcState] = useState<EACState>(ACStateManager.getACState());

  useEffect(() => {
    const unregister = ACStateManager.onACStateChange(() => {
      setAcStateOverwrite(Setting.appACStateOverWrite());
      setAcState(ACStateManager.getACState());
    });

    return () => {
      unregister();
    };
  }, []);

  const getAcStateName = (state: EACState): string => {
    if (state === EACState.Connected || state === EACState.Charging) {
      return localizationManager.getString(localizeStrEnum.AC_MODE);
    } else if (state === EACState.Disconnected) {
      return localizationManager.getString(localizeStrEnum.BAT_MODE);
    }
    return localizationManager.getString(localizeStrEnum.UNKNOWN);
  };

  const getDescription = (): string => {
    return (
      localizationManager.getString(localizeStrEnum.USING) +
      (acStateOverwrite ? "『" : "") +
      (acStateOverwrite
        ? getAcStateName(acState)
        : localizationManager.getString(localizeStrEnum.DEFAULT)) +
      (acStateOverwrite ? "』" : "") +
      localizationManager.getString(localizeStrEnum.PROFILE)
    );
  };

  return (
    <PanelSectionRow>
      <ToggleField
        label={localizationManager.getString(
          localizeStrEnum.USE_PERACMODE_PROFILE
        )}
        description={getDescription()}
        checked={acStateOverwrite}
        onChange={(value) => {
          Setting.setACStateOverWrite(value);
          setAcStateOverwrite(value);
        }}
      />
    </PanelSectionRow>
  );
};

