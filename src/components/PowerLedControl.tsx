import { PanelSectionRow, ToggleField } from "@decky/ui";
import { FC, useEffect, useState } from "react";
import { localizationManager, localizeStrEnum } from "../i18n";
import { Backend, Logger } from "../util";
import { Setting } from "../hooks";

export const PowerLedControl: FC = () => {
  const [supported, setSupported] = useState<boolean>(false);
  const [powerLedEnabled, setPowerLedEnabled] = useState<boolean>(
    Setting.powerLedEnabled
  );
  const [powerLedSuspendOff, setPowerLedSuspendOff] = useState<boolean>(
    Setting.powerLedSuspendOff
  );
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const init = async () => {
      try {
        // Get device capabilities | 获取设备能力
        const caps = await Backend.getDeviceCapabilities();
        setSupported(caps.power_led);

        if (caps.power_led) {
          // Get current state | 获取当前状态
          const status = await Backend.getPowerLight();
          if (status !== null) {
            setPowerLedEnabled(status);
            Setting.powerLedEnabled = status;
          }
        }
      } catch (error) {
        Logger.error(`Failed to init power LED control: ${error}`);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handlePowerLedToggle = async (value: boolean) => {
    setLoading(true);
    try {
      const success = await Backend.setPowerLight(value);
      if (success) {
        setPowerLedEnabled(value);
        Setting.powerLedEnabled = value;
      } else {
        Logger.warn("Failed to toggle power LED");
      }
    } catch (error) {
      Logger.error(`Error toggling power LED: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspendBehaviorToggle = async (value: boolean) => {
    setPowerLedSuspendOff(value);
    Setting.powerLedSuspendOff = value;
  };

  // Don't render if not supported | 不支持就不渲染
  if (!supported) return null;

  return (
    <>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(
            localizeStrEnum.POWER_LED_LABEL
          )}
          description={localizationManager.getString(
            localizeStrEnum.POWER_LED_DESC
          )}
          checked={powerLedEnabled}
          onChange={handlePowerLedToggle}
          disabled={loading}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(
            localizeStrEnum.POWER_LED_SUSPEND_OFF_LABEL
          )}
          description={localizationManager.getString(
            localizeStrEnum.POWER_LED_SUSPEND_OFF_DESC
          )}
          checked={powerLedSuspendOff}
          onChange={handleSuspendBehaviorToggle}
          disabled={!powerLedEnabled}
        />
      </PanelSectionRow>
    </>
  );
};

