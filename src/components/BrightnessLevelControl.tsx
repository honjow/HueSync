import { FC } from "react";
import { SingleDropdownOption, DropdownItem } from "@decky/ui";
import { localizationManager, localizeStrEnum } from "../i18n";

interface BrightnessLevelControlProps {
  brightnessLevel: string;
  onChange: (brightnessLevel: string) => void;
}

export const BrightnessLevelControl: FC<BrightnessLevelControlProps> = ({ brightnessLevel, onChange }) => {
  const brightnessLevelOptions: SingleDropdownOption[] = [
    { label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_LOW), data: "low" },
    { label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_MEDIUM), data: "medium" },
    { label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_HIGH), data: "high" },
  ];

  return (
    <DropdownItem
      label={localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL)}
      strDefaultLabel={localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_DESC)}
      selectedOption={brightnessLevelOptions.find((opt) => opt.data === brightnessLevel)?.data}
      rgOptions={brightnessLevelOptions}
      onChange={(option) => {
        onChange(option.data as string);
      }}
    />
  );
};

