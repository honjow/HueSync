import { FC } from "react";
import { SingleDropdownOption, DropdownItem, PanelSectionRow } from "@decky/ui";
import { localizationManager, localizeStrEnum } from "../i18n";

interface SpeedControlProps {
  speed: string;
  onChange: (speed: string) => void;
}

export const SpeedControl: FC<SpeedControlProps> = ({ speed, onChange }) => {
  const speedOptions: SingleDropdownOption[] = [
    {
      label: localizationManager.getString(localizeStrEnum.SPEED_LOW) || "Slow",
      data: "low",
    },
    {
      label: localizationManager.getString(localizeStrEnum.SPEED_MEDIUM) || "Medium",
      data: "medium",
    },
    {
      label: localizationManager.getString(localizeStrEnum.SPEED_HIGH) || "Fast",
      data: "high",
    },
  ];

  return (
    <PanelSectionRow>
      <DropdownItem
        label={localizationManager.getString(localizeStrEnum.SPEED) || "Speed"}
        strDefaultLabel={localizationManager.getString(localizeStrEnum.SPEED_DESC) || "Animation Speed"}
        selectedOption={speedOptions.find((opt) => opt.data === speed)?.data}
        rgOptions={speedOptions}
        onChange={(option) => {
          onChange(option.data as string);
        }}
      />
    </PanelSectionRow>
  );
};

