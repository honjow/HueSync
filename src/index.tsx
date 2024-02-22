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
import { Backend } from "./backend";
import { Setting } from "./settings";
import { SlowSliderField } from "./SlowSliderField";
import { Canvas } from "./canvas";
import { localizeStrEnum, localizationManager } from "./i18n";

const Content: VFC = () => {
  const [enableControl, setEnableControl] = useState<boolean>(
    Setting.getEnableControl()
  );
  const [ledOn, setledOn] = useState<boolean>(Setting.getLedOn());
  const [currentTargetRed, setCurrentTargetRed] = useState<number>(
    Setting.getRed()
  );
  const [currentTargetGreen, setCurrentTargetGreen] = useState<number>(
    Setting.getGreen()
  );
  const [currentTargetBlue, setCurrentTargetBlue] = useState<number>(
    Setting.getBlue()
  );
  const [currentTargetBrightness, setCurrentTargetBrightness] = useState<number>(
    Setting.getBrightness()
  );
  const [currentMark, setCurrentMark] = useState<number>(0);

  function onClickCanvas(e: any) {
    //console.log("canvas click", e);
    const realEvent: any = e.nativeEvent;
    //console.log("Canvas click @ (" + realEvent.layerX.toString() + ", " + realEvent.layerY.toString() + ")");
    const target: any = e.currentTarget;
    //console.log("Target dimensions " + target.width.toString() + "x" + target.height.toString());
    const clickX = realEvent.layerX;
    setCurrentMark(clickX);
    const cellwidth = target.width / 150;
    var j = clickX / cellwidth;
    //console.log("j " + j.toString());
    var r = 255,
      g = 0,
      b = 0;
    for (var i = 0; i < 150; i++) {
      if (i < 25) {
        g += 10;
      } else if (i > 25 && i < 50) {
        r -= 10;
      } else if (i > 50 && i < 75) {
        g -= 10;
        b += 10;
      } else if (i > 75 && i < 100) {
        r += 10;
      } else {
        b -= 10;
        if (b < 0) b = 0;
      }

      if (i >= j) {
        setCurrentTargetRed(r);
        setCurrentTargetGreen(g);
        setCurrentTargetBlue(b);
        break;
      }
    }
  }

  function drawCanvas(ctx: any, frameCount: number): void {
    if (frameCount % 100 > 1) {
      return;
    }
    const width: number = ctx.canvas.width;
    const height: number = ctx.canvas.height;
    const cellwidth = width / 150;
    var r = 255,
      g = 0,
      b = 0;
    for (var i = 0; i < 150; i++) {
      if (i < 25) {
        g += 10;
      } else if (i > 25 && i < 50) {
        r -= 10;
      } else if (i > 50 && i < 75) {
        g -= 10;
        b += 10;
      } else if (i > 75 && i < 100) {
        r += 10;
      } else {
        b -= 10;
      }

      ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
      ctx.fillRect(cellwidth * i, 0, cellwidth, height);
    }

    if (currentMark > 0) {
      ctx.beginPath();
      ctx.fillStyle = "#000000";
      ctx.moveTo(currentMark, 0);
      ctx.lineTo(currentMark + 4, 0);
      ctx.lineTo(currentMark + 2, 4);
      ctx.fill();
      console.log("fill Mark " + currentMark.toString());
    }
  }

  useEffect(() => {
    Setting.setEnableControl(enableControl);
  }, [enableControl]);

  useEffect(() => {
    if (ledOn) {
      Setting.setLedOn(currentTargetRed, currentTargetGreen, currentTargetBlue, currentTargetBrightness);
    } else {
      Setting.setOff();
    }
  }, [ledOn]);

  useEffect(() => {
    Setting.setRed(currentTargetRed);
    Setting.setGreen(currentTargetGreen);
    Setting.setBlue(currentTargetBlue);
    Setting.setBrightness(currentTargetBrightness);
  }, [currentTargetRed, currentTargetGreen, currentTargetBlue, currentTargetBrightness]);

  return (
    <PanelSection title={localizationManager.getString(localizeStrEnum.TITEL_SETTINGS)}>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(localizeStrEnum.ENABLE_LED_CONTROL)}
          checked={enableControl}
          onChange={(value) => {
            setEnableControl(value);
          }}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={localizationManager.getString(localizeStrEnum.LED_ON)}
          checked={ledOn}
          onChange={(value) => {
            setledOn(value);
          }}
        />
      </PanelSectionRow>
      {ledOn && (
        <PanelSectionRow>
          <Canvas
            draw={drawCanvas}
            width={268}
            height={48}
            style={{
              width: "268px",
              height: "48px",
              padding: "0px",
              border: "2px solid #1a9fff",
              //"position":"relative",
              "background-color": "#1a1f2c",
              "border-radius": "6px",
              // "margin":"auto",
            }}
            onClick={(e: any) => onClickCanvas(e)}
          />
        </PanelSectionRow>
      )}
      {ledOn && (
        <PanelSectionRow>
          <SlowSliderField
            label={localizationManager.getString(localizeStrEnum.BRIGHTNESS)}
            value={currentTargetBrightness}
            step={1}
            max={100}
            min={0}
            showValue={true}
            onChangeEnd={(value: number) => {
              setCurrentTargetBrightness(value);
            }}
          />
        </PanelSectionRow>
      )}
      {ledOn && (
        <PanelSectionRow>
          <SlowSliderField
            label={localizationManager.getString(localizeStrEnum.RED)}
            value={currentTargetRed}
            step={1}
            max={255}
            min={0}
            showValue={true}
            onChangeEnd={(value: number) => {
              setCurrentTargetRed(value);
            }}
          />
        </PanelSectionRow>
      )}
      {ledOn && (
        <PanelSectionRow>
          <SlowSliderField
            label={localizationManager.getString(localizeStrEnum.GREEN)}
            value={currentTargetGreen}
            step={1}
            max={255}
            min={0}
            showValue={true}
            onChangeEnd={(value: number) => {
              setCurrentTargetGreen(value);
            }}
          />
        </PanelSectionRow>
      )}
      {ledOn && (
        <PanelSectionRow>
          <SlowSliderField
            label={localizationManager.getString(localizeStrEnum.BLUE)}
            value={currentTargetBlue}
            step={1}
            max={255}
            min={0}
            showValue={true}
            onChangeEnd={(value: number) => {
              setCurrentTargetBlue(value);
            }}
          />
        </PanelSectionRow>
      )}
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
    title: <div className={staticClasses.Title}>ayaled</div>,
    content: <Content />,
    icon: <FaLightbulb />,
    onDismount() {},
  };
});
