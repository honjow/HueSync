// MSI Custom RGB Editor Modal
// MSI 自定义 RGB 编辑器弹窗

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
  FiChevronLeft,
  FiChevronRight,
  FiPlus,
  FiTrash2,
  FiEye,
} from "react-icons/fi";
import { useMsiCustomRgb } from "../hooks";
import { MsiLEDPreview } from "./MsiLEDPreview";
import { MSI_LED_ZONE_KEYS, MSI_MAX_KEYFRAMES } from "../util/const";
import { RGBTuple } from "../types/msiCustomRgb";
import { hsvToRgb, rgbToHsv } from "../util";
import { SlowSliderField } from "./SlowSliderField";
import { localizationManager, localizeStrEnum } from "../i18n";

interface MsiCustomRgbEditorProps {
  closeModal: () => void;
}

export const MsiCustomRgbEditor: FC<MsiCustomRgbEditorProps> = ({ closeModal }) => {
  const {
    editing,
    editingName,
    updateZoneColor,
    addKeyframe,
    deleteKeyframe,
    updateSpeed,
    updateBrightness,
    preview,
    save,
    cancelEditing,
  } = useMsiCustomRgb();

  const [currentFrame, setCurrentFrame] = useState(0);
  const [selectedZone, setSelectedZone] = useState(0);
  const [presetName, setPresetName] = useState(editingName || "");
  const [isSaving, setIsSaving] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);

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
          padding: "10px 12px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          margin: "0 4px",
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
    if (editing.keyframes.length < MSI_MAX_KEYFRAMES) {
      addKeyframe(currentFrame);
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

  const handlePreview = async () => {
    setIsPreviewing(true);
    try {
      await preview();
    } finally {
      setIsPreviewing(false);
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

  const handleCancel = () => {
    cancelEditing();
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
          marginBlockEnd: "20px",
          marginBlockStart: "0px",
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          padding: "8px 0",
          gap: "16px",
        }}
      >
        {/* Left: Preview and zone selection */}
        <div style={{ display: "flex", flexDirection: "column" }}>
          <MsiLEDPreview
            keyframes={editing!.keyframes}
            currentFrame={currentFrame}
            selectedZone={selectedZone}
          />

          {/* Zone selection slider */}
          <div style={{ marginTop: "8px" }}>
            <SlowSliderField
              value={selectedZone}
              min={0}
              max={8}
              step={1}
              onChange={handleZoneChange}
              notchCount={9}
              notchLabels={MSI_LED_ZONE_KEYS.map((_, idx) => ({
                notchIndex: idx,
                label: `${idx + 1}`,
                value: idx,
              }))}
              notchTicksVisible={true}
              showValue={false}
            />
            <div style={{ fontSize: "12px", color: "#93979C", marginTop: "4px", paddingLeft: "8px" }}>
              {localizationManager.getString(localizeStrEnum[MSI_LED_ZONE_KEYS[selectedZone] as keyof typeof localizeStrEnum])}
            </div>
          </div>

          {/* Frame navigation with icons */}
          <Field
            label={`${localizationManager.getString(localizeStrEnum.MSI_CUSTOM_KEYFRAME_LABEL)} ${currentFrame + 1} / ${editing!.keyframes.length}`}
            childrenLayout="below"
            highlightOnFocus={false}
          >
            {/* @ts-ignore */}
            <Focusable
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "space-evenly",
                padding: "0 4px",
              }}
            >
              <FrameControlButton
                onOKActionDescription="PREV"
                onClick={() => setCurrentFrame(Math.max(0, currentFrame - 1))}
                disabled={currentFrame === 0}
              >
                <FiChevronLeft />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription="NEXT"
                onClick={() =>
                  setCurrentFrame(Math.min(editing!.keyframes.length - 1, currentFrame + 1))
                }
                disabled={currentFrame >= editing!.keyframes.length - 1}
              >
                <FiChevronRight />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription="ADD"
                onClick={handleAddFrame}
                disabled={editing!.keyframes.length >= MSI_MAX_KEYFRAMES}
              >
                <FiPlus />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription="DELETE"
                onClick={handleDeleteFrame}
                disabled={editing!.keyframes.length <= 1}
              >
                <FiTrash2 />
              </FrameControlButton>
              <FrameControlButton
                onOKActionDescription="PREVIEW"
                onClick={handlePreview}
                disabled={isPreviewing}
              >
                <FiEye />
              </FrameControlButton>
            </Focusable>
          </Field>
        </div>

        {/* Right: HSV Controls */}
        <div
          style={{
            width: "300px",
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
              <div style={{ fontSize: "12px", color: "#93979C", marginTop: "8px" }}>
                {localizationManager.getString(localizeStrEnum.MSI_CUSTOM_KEYFRAMES_INFO)}: {editing!.keyframes.length} / {MSI_MAX_KEYFRAMES}
              </div>
            </PanelSection>

            {/* CSS for HSV sliders */}
            <style>
              {`
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
          padding: "8px 0",
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
