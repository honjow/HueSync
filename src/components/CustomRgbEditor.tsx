// Unified Custom RGB Editor Modal
// 统一的自定义 RGB 编辑器弹窗
// Supports MSI Claw, AyaNeo, and other multi-zone LED devices
// 支持 MSI Claw、AyaNeo 等多区域 LED 设备

import { FC, useState, useEffect } from "react";
import {
  ModalRoot,
  PanelSection,
  TextField,
  DialogButton,
  Field,
  Focusable,
  gamepadSliderClasses,
} from "@decky/ui";
import {
  FiPlus,
  FiTrash2,
  FiPlay,
  FiPause,
  FiCopy,
  FiRotateCw,
  FiRotateCcw,
  FiDroplet,
} from "react-icons/fi";
import { useCustomRgb } from "../hooks";
import { MsiLEDPreview } from "./CustomLEDPreview";
import { 
  MSI_LED_ZONE_KEYS, MSI_MAX_KEYFRAMES, 
  AYANEO_LED_ZONE_KEYS_8, AYANEO_LED_ZONE_KEYS_9_KUN, AYANEO_MAX_KEYFRAMES,
  ALLY_LED_ZONE_KEYS, ALLY_MAX_KEYFRAMES,
  RGBMode 
} from "../util/const";
import { RGBTuple } from "../types/customRgb";
import { hsvToRgb, rgbToHsv } from "../util";
import { SlowSliderField } from "./SlowSliderField";
import { localizationManager, localizeStrEnum } from "../i18n";
import { Backend } from "../util/backend";
import { MSI_CLAW_LAYOUT, AYANEO_STANDARD_LAYOUT, AYANEO_KUN_LAYOUT, ROG_ALLY_LAYOUT } from "../util/ledLayouts";
import { Setting } from "../hooks/settings";
import { CustomRgbDeviceType } from "../types/customRgb";

type DeviceType = CustomRgbDeviceType; // Unified type from customRgb.d.ts

interface CustomRgbEditorProps {
  closeModal: () => void;
  deviceType?: DeviceType; // Device type: "msi" or "ayaneo"
}

export const CustomRgbEditor: FC<CustomRgbEditorProps> = ({ 
  closeModal,
  deviceType = "msi" // Default to MSI for backward compatibility
}) => {
  // Use unified custom RGB hook (automatically selects correct implementation)
  // 使用统一的自定义 RGB hook（自动选择正确的实现）
  const hook = useCustomRgb();
  
  const {
    editing,
    editingName,
    updateZoneColor,
    addKeyframe,
    deleteKeyframe,
    updateSpeed,
    updateBrightness,
    updateConfig,
    preview,
    previewSingleFrame,
    save,
    cancelEditing,
    applyPreset,
  } = hook;

  // Device-specific configuration
  // 设备特定配置
  const DEVICE_CONFIGS = {
    msi: {
      zoneKeys: MSI_LED_ZONE_KEYS,
      maxKeyframes: MSI_MAX_KEYFRAMES,
      layout: MSI_CLAW_LAYOUT,
    },
    rog_ally: {
      zoneKeys: ALLY_LED_ZONE_KEYS,
      maxKeyframes: ALLY_MAX_KEYFRAMES,
      layout: ROG_ALLY_LAYOUT,
    },
    ayaneo_8: {
      zoneKeys: AYANEO_LED_ZONE_KEYS_8,
      maxKeyframes: AYANEO_MAX_KEYFRAMES,
      layout: AYANEO_STANDARD_LAYOUT,
    },
    ayaneo_9: {
      zoneKeys: AYANEO_LED_ZONE_KEYS_9_KUN,
      maxKeyframes: AYANEO_MAX_KEYFRAMES,
      layout: AYANEO_KUN_LAYOUT,
    },
  };

  // Select appropriate configuration based on device type
  // 根据设备类型选择适当的配置
  const config = (() => {
    if (deviceType === "ayaneo") {
      const zoneCount = editing?.keyframes[0]?.length || 8;
      return zoneCount === 9 ? DEVICE_CONFIGS.ayaneo_9 : DEVICE_CONFIGS.ayaneo_8;
    }
    return DEVICE_CONFIGS[deviceType];
  })();

  const [currentFrame, setCurrentFrame] = useState(0);
  const [selectedZone, setSelectedZone] = useState(0);
  const [presetName, setPresetName] = useState(editingName || "");
  const [isSaving, setIsSaving] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  if (!editing) {
    return null;
  }

  // Get current color as RGB
  const currentColor = editing.keyframes[currentFrame][selectedZone];
  const [r, g, b] = currentColor;

  // Maintain independent HSV state to preserve hue when saturation/value is 0
  const [hsvState, setHsvState] = useState<[number, number, number]>(() => {
    const [h, s, v] = rgbToHsv(r, g, b);
    // Default to black: hue 0, saturation 100, value 0
    return s === 0 && v === 0 ? [0, 100, 0] : [h, s, v];
  });

  // Update HSV state when frame, zone, or color changes
  useEffect(() => {
    const [h, s, v] = rgbToHsv(r, g, b);
    // Preserve current hue if color is grayscale (saturation = 0)
    // This allows user to adjust saturation without losing hue value
    if (s === 0 && hsvState[1] > 0) {
      // Keep existing hue, update saturation and value
      setHsvState([hsvState[0], s, v]);
    } else {
      setHsvState([h, s, v]);
    }
  }, [currentFrame, selectedZone]);

  // Auto-preview current frame when not playing
  useEffect(() => {
    if (isPlaying || !editing) return;
    
    const timer = setTimeout(() => {
      previewSingleFrame(currentFrame);
    }, 300); // 300ms debounce to avoid frequent updates
    
    return () => clearTimeout(timer);
  }, [currentFrame, editing, isPlaying]);

  // Re-send all frames when playing and config changes (speed, brightness, or any frame color)
  useEffect(() => {
    if (!isPlaying || !editing) return;
    
    const timer = setTimeout(() => {
      preview();
    }, 300); // 300ms debounce to avoid frequent updates
    
    return () => clearTimeout(timer);
  }, [editing, isPlaying]);

  const [hue, saturation, value] = hsvState;

  // Frame control button component
  interface FrameControlButtonProps {
    onOKActionDescription: string;
    onClick?: () => void;
    disabled?: boolean;
    children?: React.ReactNode;
  }

  const FrameControlButton = ({
    onOKActionDescription,
    onClick,
    children,
    disabled,
  }: FrameControlButtonProps) => {
    return (
      <DialogButton
        style={{
          height: "32px",
          flex: "1",
          minWidth: 0,
          padding: "8px 8px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          margin: "0 2px",
        }}
        disabled={disabled}
        onOKActionDescription={onOKActionDescription}
        onClick={onClick}
      >
        {children}
      </DialogButton>
    );
  };

  const handleZoneChange = (zone: number) => {
    setSelectedZone(zone);
  };

  const handleHsvChange = (h: number, s: number, v: number) => {
    // Update HSV state to preserve hue even when saturation/value is 0
    setHsvState([h, s, v]);
    
    // Convert HSV to RGB and update color
    const [newR, newG, newB] = hsvToRgb(h, s, v);
    const newColor: RGBTuple = [newR, newG, newB];
    updateZoneColor(currentFrame, selectedZone, newColor);
  };

  const handleAddFrame = () => {
    if (editing.keyframes.length < config.maxKeyframes) {
      addKeyframe(); // Create a new black frame
      setCurrentFrame(editing.keyframes.length);
    }
  };

  const handleDeleteFrame = () => {
    if (editing.keyframes.length > 1) {
      deleteKeyframe(currentFrame);
      if (currentFrame >= editing.keyframes.length - 1) {
        setCurrentFrame(Math.max(0, currentFrame - 1));
      }
    }
  };

  const rotateFrame = (frame: RGBTuple[], clockwise: boolean): RGBTuple[] => {
    const newFrame = [...frame];
    const rotationMappings = config.layout.rotationMappings;
    
    // Find left and right zones from layout using circle identifier
    const leftZones = config.layout.zoneMappings
      .filter(z => z.circle === "leftStick")
      .sort((a, b) => a.arrayIndex - b.arrayIndex)
      .map(z => z.arrayIndex);
    
    const rightZones = config.layout.zoneMappings
      .filter(z => z.circle === "rightStick")
      .sort((a, b) => a.arrayIndex - b.arrayIndex)
      .map(z => z.arrayIndex);
    
    // Apply rotation to right stick (支持 2 或 4 个 zones)
    if (rightZones.length >= 2 && rotationMappings?.rightStick) {
      const mapping = clockwise ? rotationMappings.rightStick.clockwise : rotationMappings.rightStick.counterClockwise;
      const rightColors = rightZones.map(idx => frame[idx]);
      // mapping[sourceIdx] = targetArrayIndex
      mapping.forEach((targetArrayIndex: number, sourceIdx: number) => {
        newFrame[targetArrayIndex] = rightColors[sourceIdx];
      });
    }
    
    // Apply rotation to left stick (支持 2 或 4 个 zones)
    if (leftZones.length >= 2 && rotationMappings?.leftStick) {
      const mapping = clockwise ? rotationMappings.leftStick.clockwise : rotationMappings.leftStick.counterClockwise;
      const leftColors = leftZones.map(idx => frame[idx]);
      // mapping[sourceIdx] = targetArrayIndex
      mapping.forEach((targetArrayIndex: number, sourceIdx: number) => {
        newFrame[targetArrayIndex] = leftColors[sourceIdx];
      });
    }
    
    // Center button (ABXY/Guide) remains unchanged
    
    return newFrame;
  };

  const handleCopyFrame = () => {
    if (editing && editing.keyframes.length < config.maxKeyframes) {
      addKeyframe(currentFrame);
      setCurrentFrame(editing.keyframes.length);
    }
  };

  const handleCopyRotateCW = () => {
    if (!editing || editing.keyframes.length >= config.maxKeyframes) return;
    
    const rotated = rotateFrame(editing.keyframes[currentFrame], true);
    const newConfig = { ...editing };
    newConfig.keyframes = [...newConfig.keyframes, rotated];
    updateConfig(newConfig);
    setCurrentFrame(newConfig.keyframes.length - 1);
  };

  const handleCopyRotateCCW = () => {
    if (!editing || editing.keyframes.length >= config.maxKeyframes) return;
    
    const rotated = rotateFrame(editing.keyframes[currentFrame], false);
    const newConfig = { ...editing };
    newConfig.keyframes = [...newConfig.keyframes, rotated];
    updateConfig(newConfig);
    setCurrentFrame(newConfig.keyframes.length - 1);
  };

  const handleFillAllZones = () => {
    if (!editing) return;
    
    // Get the current color of the selected zone
    const currentColor = editing.keyframes[currentFrame][selectedZone];
    
    // Create a new frame with all zones set to the current color
    const newFrame = Array(config.zoneKeys.length).fill(null).map(() => [...currentColor] as RGBTuple);
    
    // Update the current frame
    const newConfig = { ...editing };
    newConfig.keyframes = [...newConfig.keyframes];
    newConfig.keyframes[currentFrame] = newFrame;
    
    updateConfig(newConfig);
    
    // Preview the updated frame if not playing
    if (!isPlaying) {
      previewSingleFrame(currentFrame);
    }
  };

  const togglePlayback = async () => {
    if (isPlaying) {
      // Pause: stop playback and return to current frame preview
      setIsPlaying(false);
      await previewSingleFrame(currentFrame);
    } else {
      // Play: send all frames for animation
      setIsPlaying(true);
      await preview();
    }
  };

  const handleSave = async () => {
    if (!presetName.trim()) {
      alert("Please enter preset name");
      return;
    }

    setIsSaving(true);
    try {
      const success = await save(presetName.trim());
      if (success) {
        closeModal();
      } else {
        alert("Save failed");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = async () => {
    cancelEditing();
    
    // Restore the device to the state before editing
    // 恢复设备到编辑前的状态
    // For custom mode, need to reapply the active preset; for standard modes, use applySettings
    // 对于自定义模式，需要重新应用激活的 preset；对于标准模式，使用 applySettings
    if (Setting.mode === RGBMode.custom && Setting.currentCustomPreset) {
      // Reapply the previously active preset
      await applyPreset(Setting.currentCustomPreset);
    } else {
      // Standard mode (or no active custom preset)
      await Backend.applySettings();
    }
    
    closeModal();
  };

  return (
    <ModalRoot onCancel={handleCancel} onEscKeypress={handleCancel}>
      <h1
        style={{
          marginBlockEnd: "5px",
          marginBlockStart: "-15px",
          fontSize: 20,
        }}
      >
        <TextField
          label={editingName ? localizationManager.getString(localizeStrEnum.MSI_CUSTOM_EDIT_EFFECT) : localizationManager.getString(localizeStrEnum.MSI_CUSTOM_NEW_EFFECT)}
          value={presetName}
          onChange={(e) => setPresetName((e.target as HTMLInputElement).value)}
        />
      </h1>
      <div
        style={{
          marginBlockEnd: "8px",
          marginBlockStart: "0px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          padding: "4px 2px",
          gap: "16px",
        }}
      >
        {/* Left: Preview and zone selection */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <MsiLEDPreview
            keyframes={editing!.keyframes}
            currentFrame={currentFrame}
            selectedZone={selectedZone}
            onZoneClick={setSelectedZone}
            isPlaying={isPlaying}
            speed={editing!.speed}
            brightness={editing!.brightness}
            layoutConfig={config.layout}
          />

          {/* Zone selection slider */}
          <div style={{ 
            // padding: "8px 0",
            width: "280px"
          }}
          >
            <SlowSliderField
              value={selectedZone}
              min={0}
              max={config.zoneKeys.length - 1}
              step={1}
              onChange={handleZoneChange}
              notchCount={config.zoneKeys.length}
              notchLabels={config.zoneKeys.map((_, idx) => ({
                notchIndex: idx,
                label: `${idx + 1}`,
                value: idx,
              }))}
              notchTicksVisible={true}
              showValue={false}
            />
            <div style={{ fontSize: "12px", color: "#93979C", marginTop: "4px", paddingLeft: "8px" }}>
              {localizationManager.getString(localizeStrEnum[config.zoneKeys[selectedZone] as keyof typeof localizeStrEnum])}
            </div>
          </div>

          {/* Keyframe color timeline */}
          <div style={{ 
            marginTop: "4px", 
            marginBottom: "4px"
            }}
          >
            <div style={{ 
              fontSize: "10px", 
              color: "#B8BCBF", 
              marginBottom: "4px",
              textAlign: "center"
            }}>
              {localizationManager.getString(localizeStrEnum.MSI_CUSTOM_KEYFRAME_LABEL)} {currentFrame + 1} / {editing!.keyframes.length}
            </div>
            {/* @ts-ignore */}
            <Focusable
              style={{ 
                display: "flex", 
                gap: editing!.keyframes.length > 4 ? "6px" : "12px",
                alignItems: "center",
                justifyContent: "center",
                padding: "4px 8px",
                minHeight: "26px"
              }}
            >
              {editing!.keyframes.map((frame: RGBTuple[], index: number) => {
                // Find the brightest/most saturated color to represent this frame
                const nonBlackColors = frame.filter((rgb: RGBTuple) => rgb[0] + rgb[1] + rgb[2] > 30);
                let representativeColor = [40, 40, 40]; // Default dark gray
                
                if (nonBlackColors.length > 0) {
                  // Sort by brightness (sum of RGB) and saturation (max - min of RGB)
                  representativeColor = nonBlackColors.reduce((brightest: RGBTuple, current: RGBTuple) => {
                    const brightnessCurrent = current[0] + current[1] + current[2];
                    const brightnessBrightest = brightest[0] + brightest[1] + brightest[2];
                    const saturationCurrent = Math.max(...current) - Math.min(...current);
                    const saturationBrightest = Math.max(...brightest) - Math.min(...brightest);
                    
                    // Prefer high saturation first, then brightness
                    if (saturationCurrent > saturationBrightest || 
                       (saturationCurrent === saturationBrightest && brightnessCurrent > brightnessBrightest)) {
                      return current;
                    }
                    return brightest;
                  });
                }
                
                const [r, g, b] = representativeColor;
                const isCurrent = currentFrame === index;
                
                return (
                  // @ts-ignore
                  <Focusable
                    key={index}
                    onActivate={() => setCurrentFrame(index)}
                    noFocusRing={true}
                    style={{
                      width: "18px",
                      height: "18px",
                      background: `rgb(${r}, ${g}, ${b})`,
                      borderRadius: "3px",
                      border: isCurrent ? "2px solid #1A9FFF" : "2px solid #666",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      boxShadow: isCurrent ? "0 0 6px rgba(26, 159, 255, 0.6)" : "none",
                      flexShrink: 0,
                      opacity: isCurrent ? 1 : 0.7,
                    }}
                    focusClassName="keyframe-focused"
                  />
                );
              })}
            </Focusable>
          </div>

          {/* Frame navigation with icons */}
          <Field
            label=""
            childrenLayout="below"
            highlightOnFocus={false}
            padding="none"
          >
            {/* @ts-ignore */}
            <Focusable
              style={{
                // width: "100%",
                width: "280px",
                display: "flex",
                justifyContent: "space-evenly",
                padding: "6px 4px",
              }}
            >
              <FrameControlButton
                onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_ADD_FRAME)}
                onClick={handleAddFrame}
                disabled={editing!.keyframes.length >= config.maxKeyframes}
              >
                <FiPlus />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_COPY_FRAME)}
                onClick={handleCopyFrame}
                disabled={editing!.keyframes.length >= config.maxKeyframes}
              >
                <FiCopy />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_FILL_ALL_ZONES)}
                onClick={handleFillAllZones}
                disabled={!editing}
              >
                <FiDroplet />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_COPY_ROTATE_CW)}
                onClick={handleCopyRotateCW}
                disabled={editing!.keyframes.length >= config.maxKeyframes}
              >
                <FiRotateCw />
              </FrameControlButton>
              {/* 只在有 4 个 LED 时显示逆时针按钮 (2 个 LED 时顺逆时针相同) */}
              {(() => {
                const hasMoreThanTwoLeds = config.layout.zoneMappings
                  .filter(z => z.circle === "leftStick").length > 2 ||
                  config.layout.zoneMappings
                  .filter(z => z.circle === "rightStick").length > 2;
                
                return hasMoreThanTwoLeds && (
                  <FrameControlButton
                    onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_COPY_ROTATE_CCW)}
                    onClick={handleCopyRotateCCW}
                    disabled={editing!.keyframes.length >= config.maxKeyframes}
                  >
                    <FiRotateCcw />
                  </FrameControlButton>
                );
              })()}
              <FrameControlButton
                onOKActionDescription={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_DELETE_FRAME)}
                onClick={handleDeleteFrame}
                disabled={editing!.keyframes.length <= 1}
              >
                <FiTrash2 />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription={isPlaying ? localizationManager.getString(localizeStrEnum.MSI_CUSTOM_PAUSE) : localizationManager.getString(localizeStrEnum.MSI_CUSTOM_PLAY)}
                onClick={togglePlayback}
              >
                {isPlaying ? <FiPause /> : <FiPlay />}
              </FrameControlButton>
            </Focusable>
          </Field>
        </div>

        {/* Right: HSV Controls */}
        <div
          style={{
            width: "280px",
            height: "280px",
            overflowX: "hidden",
            overflowY: "scroll",
          }}
        >
            <PanelSection title={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_COLOR_EDITOR)}>
              {/* Hue slider with rainbow gradient */}
              <SlowSliderField
                showValue
                label={localizationManager.getString(localizeStrEnum.HUE)}
                value={hue}
                min={0}
                max={359}
                validValues="range"
                onChangeEnd={(h) => handleHsvChange(h, saturation, value)}
                onChange={(h) => handleHsvChange(h, saturation, value)}
                className="MsiColorPicker_HSlider"
                valueSuffix="°"
              />

              {/* Saturation slider with gradient */}
              <SlowSliderField
                showValue
                label={localizationManager.getString(localizeStrEnum.SATURATION)}
                value={saturation}
                min={0}
                max={100}
                validValues="range"
                onChangeEnd={(s) => handleHsvChange(hue, s, value)}
                onChange={(s) => handleHsvChange(hue, s, value)}
                valueSuffix="%"
                className="MsiColorPicker_SSlider"
              />

              {/* Value/Brightness slider with gradient */}
              <SlowSliderField
                showValue
                label={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_VALUE)}
                value={value}
                min={0}
                max={100}
                onChangeEnd={(v) => handleHsvChange(hue, saturation, v)}
                onChange={(v) => handleHsvChange(hue, saturation, v)}
                valueSuffix="%"
                className="MsiColorPicker_VSlider"
              />

            </PanelSection>

            <PanelSection title={localizationManager.getString(localizeStrEnum.MSI_CUSTOM_GLOBAL_SETTINGS)}>
              {/* Speed */}
              <SlowSliderField
                label={localizationManager.getString(localizeStrEnum.SPEED)}
                value={editing!.speed}
                min={0}
                max={20}
                step={1}
                onChange={updateSpeed}
                showValue={true}
              />

              {/* Brightness */}
              <SlowSliderField
                label={localizationManager.getString(localizeStrEnum.BRIGHTNESS)}
                value={editing!.brightness}
                min={0}
                max={100}
                step={1}
                onChange={updateBrightness}
                valueSuffix="%"
                showValue={true}
              />

              {/* Info */}
              {/* <div style={{ fontSize: "12px", color: "#93979C", marginTop: "8px" }}>
                {localizationManager.getString(localizeStrEnum.MSI_CUSTOM_KEYFRAMES_INFO)}: {editing!.keyframes.length} / {config.maxKeyframes}
              </div> */}
            </PanelSection>

            {/* CSS for HSV sliders and keyframe timeline */}
            <style>
              {`
                .keyframe-focused {
                  transform: scale(1.15);
                  filter: brightness(1.2);
                  outline: 2px solid #fff !important;
                  outline-offset: 2px;
                  box-shadow: 0 0 12px rgba(255, 255, 255, 0.9) !important;
                }
                
                .MsiColorPicker_HSlider .${gamepadSliderClasses.SliderTrack} {
                  background: linear-gradient(
                    to right,
                    hsl(0, 100%, 50%),
                    hsl(60, 100%, 50%),
                    hsl(120, 100%, 50%),
                    hsl(180, 100%, 50%),
                    hsl(240, 100%, 50%),
                    hsl(300, 100%, 50%),
                    hsl(360, 100%, 50%)
                  ) !important;
                  --left-track-color: #0000 !important;
                  --colored-toggles-main-color: #0000 !important;
                }
                .MsiColorPicker_SSlider .${gamepadSliderClasses.SliderTrack} {
                  background: linear-gradient(
                    to right,
                    hsl(0, 0%, 50%),
                    hsl(${hue}, 100%, 50%)
                  ) !important;
                  --left-track-color: #0000 !important;
                  --colored-toggles-main-color: #0000 !important;
                }
                .MsiColorPicker_VSlider .${gamepadSliderClasses.SliderTrack} {
                  background: linear-gradient(
                    to right,
                    hsl(0, 0%, 0%),
                    hsl(${hue}, ${saturation}%, 50%)
                  ) !important;
                  --left-track-color: #0000 !important;
                  --colored-toggles-main-color: #0000 !important;
                }
              `}
            </style>
        </div>
      </div>

      {/* Footer buttons */}
      {/* @ts-ignore */}
      <Focusable
        style={{
          marginBlockEnd: "-25px",
          marginBlockStart: "-5px",
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gridTemplateRows: "repeat(1, 1fr)",
          gridGap: "0.5rem",
          padding: "4px 0",
        }}
      >
        <DialogButton onClick={handleCancel}>{localizationManager.getString(localizeStrEnum.MSI_CUSTOM_CANCEL)}</DialogButton>
        <DialogButton onClick={handleSave} disabled={isSaving}>
          {isSaving ? localizationManager.getString(localizeStrEnum.MSI_CUSTOM_SAVING) : localizationManager.getString(localizeStrEnum.MSI_CUSTOM_SAVE)}
        </DialogButton>
      </Focusable>
    </ModalRoot>
  );
};
