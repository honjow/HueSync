import { FC } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { SlowSliderField } from ".";

interface SpeedControlProps {
  speed: string;
  onChange: (speed: string) => void;
}

export const SpeedControl: FC<SpeedControlProps> = ({ speed, onChange }) => {
  // Map string to number: "low" -> 0, "medium" -> 1, "high" -> 2
  const speedToValue = (speedStr: string): number => {
    const map: Record<string, number> = { low: 0, medium: 1, high: 2 };
    return map[speedStr] ?? 1;
  };

  // Map number to string: 0 -> "low", 1 -> "medium", 2 -> "high"
  const valueToSpeed = (value: number): string => {
    const map: Record<number, string> = { 0: "low", 1: "medium", 2: "high" };
    return map[value] ?? "medium";
  };

  return (
    <SlowSliderField
      label={localizationManager.getString(localizeStrEnum.SPEED)}
      // description={localizationManager.getString(localizeStrEnum.SPEED_DESC)}
      value={speedToValue(speed)}
      min={0}
      max={2}
      step={1}
      notchCount={3}
      notchLabels={[
        {
          notchIndex: 0,
          label: localizationManager.getString(localizeStrEnum.SPEED_LOW),
          value: 0,
        },
        {
          notchIndex: 1,
          label: localizationManager.getString(localizeStrEnum.SPEED_MEDIUM),
          value: 1,
        },
        {
          notchIndex: 2,
          label: localizationManager.getString(localizeStrEnum.SPEED_HIGH),
          value: 2,
        },
      ]}
      notchTicksVisible={true}
      showValue={false}
      onChange={(value: number) => {
        onChange(valueToSpeed(value));
      }}
      onChangeEnd={(value: number) => {
        onChange(valueToSpeed(value));
      }}
    />
  );
};

