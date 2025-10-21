import { FC } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { SlowSliderField } from ".";

interface BrightnessLevelControlProps {
  brightnessLevel: string;
  onChange: (brightnessLevel: string) => void;
}

export const BrightnessLevelControl: FC<BrightnessLevelControlProps> = ({
  brightnessLevel,
  onChange,
}) => {
  // Map string to number: "low" -> 0, "medium" -> 1, "high" -> 2
  const levelToValue = (levelStr: string): number => {
    const map: Record<string, number> = { low: 0, medium: 1, high: 2 };
    return map[levelStr] ?? 2;
  };

  // Map number to string: 0 -> "low", 1 -> "medium", 2 -> "high"
  const valueToLevel = (value: number): string => {
    const map: Record<number, string> = { 0: "low", 1: "medium", 2: "high" };
    return map[value] ?? "high";
  };

  return (
    <SlowSliderField
      label={localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL)}
      // description={localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_DESC)}
      value={levelToValue(brightnessLevel)}
      min={0}
      max={2}
      step={1}
      notchCount={3}
      notchLabels={[
        {
          notchIndex: 0,
          label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_LOW),
          value: 0,
        },
        {
          notchIndex: 1,
          label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_MEDIUM),
          value: 1,
        },
        {
          notchIndex: 2,
          label: localizationManager.getString(localizeStrEnum.BRIGHTNESS_LEVEL_HIGH),
          value: 2,
        },
      ]}
      notchTicksVisible={true}
      showValue={false}
      onChange={(value: number) => {
        onChange(valueToLevel(value));
      }}
      onChangeEnd={(value: number) => {
        onChange(valueToLevel(value));
      }}
    />
  );
};

