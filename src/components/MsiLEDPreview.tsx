// Multi-Zone LED Preview Component
// 多区域 LED 预览组件
// Supports MSI Claw, AyaNeo, and other multi-zone LED devices

import { FC, useEffect, useRef } from "react";
import { RGBTuple } from "../types/msiCustomRgb";
import { LEDLayoutConfig } from "../types/ledLayout";
import { MSI_CLAW_LAYOUT } from "../util/ledLayouts";
import { localizationManager, localizeStrEnum } from "../i18n";

interface MsiLEDPreviewProps {
  keyframes: RGBTuple[][];
  currentFrame: number;
  selectedZone: number | null;
  onZoneClick?: (zone: number) => void;
  isPlaying?: boolean;
  speed?: number;
  brightness?: number;
  layoutConfig?: LEDLayoutConfig; // Optional: layout configuration for different devices
}

// LED colors for canvas drawing
const LED_SELECTED = "#1A9FFF";  // Steam blue for selected zone
const LED_NORMAL = "rgba(255,255,255,0.4)";

// Visual configuration interface
interface VisualConfig {
  led: {
    radius: number;
    radiusSelected: number;
    borderWidth: number;
    borderWidthSelected: number;
  };
  label: {
    distance: number;
    distanceSelected: number;
    fontSize: string;
    fontSizeBold: string;
  };
}

/**
 * Calculate relative luminance for text contrast
 * 计算相对亮度用于文字对比度
 */
const getRelativeLuminance = (r: number, g: number, b: number): number => {
  const [rs, gs, bs] = [r, g, b].map(val => {
    const s = val / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
};

/**
 * Get contrasting text color based on background luminance
 * 根据背景亮度获取对比文字颜色
 */
const getContrastColor = (r: number, g: number, b: number): string => {
  return getRelativeLuminance(r, g, b) > 0.5 ? "#000000" : "#FFFFFF";
};

/**
 * Calculate LED layout positions and parameters based on layout config
 * 根据布局配置计算 LED 位置和参数
 */
const calculateLEDLayout = (width: number, height: number, layoutConfig: LEDLayoutConfig) => {
  const params = {
    canvas: { width, height },
    padding: { left: 38, right: 38, top: 12, bottom: 12 },
    ledSpacing: 70,
    ring: { innerRadius: 20, outerRadius: 28, offsetFromEdge: 35 },
    visual: {
      led: { radius: 8, radiusSelected: 10, borderWidth: 1, borderWidthSelected: 2 },
      label: { distance: 10, distanceSelected: 12, fontSize: "8px", fontSizeBold: "bold 8px" },
    },
  };

  const centerY = height / 2;
  const leftLedLeft = params.padding.left;
  const leftLedRight = leftLedLeft + params.ledSpacing;
  const rightLedLeft = width - params.padding.right - params.ledSpacing;
  const rightLedRight = width - params.padding.right;
  const ledTop = params.padding.top;
  const ledBottom = height - params.padding.bottom;
  const leftRingX = params.padding.left + params.ring.offsetFromEdge;
  const rightRingX = width - params.padding.right - params.ring.offsetFromEdge;

  // Map position strings to actual coordinates
  const positionMap: Record<string, { x: number; y: number }> = {
    "left-top-left": { x: leftLedLeft, y: ledTop },
    "left-top-right": { x: leftLedRight, y: ledTop },
    "left-bottom-left": { x: leftLedLeft, y: ledBottom },
    "left-bottom-right": { x: leftLedRight, y: ledBottom },
    "right-top-left": { x: rightLedLeft, y: ledTop },
    "right-top-right": { x: rightLedRight, y: ledTop },
    "right-bottom-left": { x: rightLedLeft, y: ledBottom },
    "right-bottom-right": { x: rightLedRight, y: ledBottom },
    "center-abxy": { x: width / 2, y: centerY },
    "center-guide": { x: width / 2, y: centerY },
  };

  // Generate clickable zones based on layout config
  const clickableZones = layoutConfig.zoneMappings.map(mapping => ({
    x: positionMap[mapping.position].x,
    y: positionMap[mapping.position].y,
    zone: mapping.arrayIndex,
  }));

  return {
    params,
    positions: {
      centerY,
      leftLedLeft,
      leftLedRight,
      rightLedLeft,
      rightLedRight,
      ledTop,
      ledBottom,
      leftRingX,
      rightRingX,
    },
    clickableZones,
    zoneMappings: layoutConfig.zoneMappings, // Include for label lookups
  };
};

export const MsiLEDPreview: FC<MsiLEDPreviewProps> = ({
  keyframes,
  currentFrame,
  selectedZone,
  onZoneClick,
  isPlaying = false,
  speed = 10,
  brightness = 100,
  layoutConfig = MSI_CLAW_LAYOUT, // Default to MSI Claw layout for backward compatibility
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | undefined>(undefined);
  const startTimeRef = useRef<number>(0);
  const selectedZoneRef = useRef<number | null>(selectedZone);

  // Keep selectedZoneRef in sync with selectedZone prop
  // 保持 selectedZoneRef 与 selectedZone prop 同步
  useEffect(() => {
    selectedZoneRef.current = selectedZone;
  }, [selectedZone]);

  /**
   * Calculate interpolated colors between keyframes for animation
   * 计算关键帧之间的插值颜色用于动画
   */
  const getInterpolatedFrame = (progress: number): RGBTuple[] => {
    const numFrames = keyframes.length;
    if (numFrames === 1) return keyframes[0];

    // Calculate which two frames to interpolate between
    const totalProgress = progress * numFrames;
    const frameIndex = Math.floor(totalProgress);
    const frameProgress = totalProgress - frameIndex;
    
    const frame1 = keyframes[frameIndex % numFrames];
    const frame2 = keyframes[(frameIndex + 1) % numFrames];

    // Interpolate each zone's color
    return frame1.map((color1, zoneIndex) => {
      const color2 = frame2[zoneIndex];
      return [
        Math.round(color1[0] + (color2[0] - color1[0]) * frameProgress),
        Math.round(color1[1] + (color2[1] - color1[1]) * frameProgress),
        Math.round(color1[2] + (color2[2] - color1[2]) * frameProgress),
      ] as RGBTuple;
    });
  };

  /**
   * Apply brightness to colors
   * 应用亮度到颜色
   */
  const applyBrightness = (colors: RGBTuple[]): RGBTuple[] => {
    const factor = brightness / 100;
    return colors.map(color => [
      Math.round(color[0] * factor),
      Math.round(color[1] * factor),
      Math.round(color[2] * factor),
    ] as RGBTuple);
  };

  /**
   * Draw static preview with current frame
   * 绘制当前帧的静态预览
   */
  const drawPreview = () => {
    const colors = applyBrightness(keyframes[currentFrame]);
    drawPreviewWithColors(colors);
  };

  /**
   * Draw preview with specific colors
   * 使用特定颜色绘制预览
   */
  const drawPreviewWithColors = (colors: RGBTuple[], highlightZone: number | null = null) => {
    // Use provided highlightZone or fall back to selectedZone
    // 使用提供的 highlightZone 或回退到 selectedZone
    const activeZone = highlightZone !== null ? highlightZone : selectedZone;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // High DPI support for crisp rendering
    const dpr = window.devicePixelRatio || 1;
    const width = 300;
    const height = 80;
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Get layout from centralized calculation with layoutConfig
    const { params, positions, zoneMappings } = calculateLEDLayout(width, height, layoutConfig);

    // Map position strings to coordinates
    const positionMap: Record<string, { x: number; y: number }> = {
      "left-top-left": { x: positions.leftLedLeft, y: positions.ledTop },
      "left-top-right": { x: positions.leftLedRight, y: positions.ledTop },
      "left-bottom-left": { x: positions.leftLedLeft, y: positions.ledBottom },
      "left-bottom-right": { x: positions.leftLedRight, y: positions.ledBottom },
      "right-top-left": { x: positions.rightLedLeft, y: positions.ledTop },
      "right-top-right": { x: positions.rightLedRight, y: positions.ledTop },
      "right-bottom-left": { x: positions.rightLedLeft, y: positions.ledBottom },
      "right-bottom-right": { x: positions.rightLedRight, y: positions.ledBottom },
      "center-abxy": { x: width / 2, y: positions.centerY },
      "center-guide": { x: width / 2, y: positions.centerY },
    };

    // Build LED list from zoneMappings
    const leftLeds = zoneMappings
      .filter(m => m.position.startsWith("left-"))
      .map(m => ({
        x: positionMap[m.position].x,
        y: positionMap[m.position].y,
        idx: m.arrayIndex,
        label: localizationManager.getString(localizeStrEnum[m.labelKey as keyof typeof localizeStrEnum]),
      }));
    
    const rightLeds = zoneMappings
      .filter(m => m.position.startsWith("right-"))
      .map(m => ({
        x: positionMap[m.position].x,
        y: positionMap[m.position].y,
        idx: m.arrayIndex,
        label: localizationManager.getString(localizeStrEnum[m.labelKey as keyof typeof localizeStrEnum]),
      }));
    
    // Find center button (ABXY or Guide)
    const centerMapping = zoneMappings.find(m => m.position.startsWith("center-"));
    const centerButton = centerMapping ? {
      x: positionMap[centerMapping.position].x,
      y: positionMap[centerMapping.position].y,
      idx: centerMapping.arrayIndex,
      label: localizationManager.getString(localizeStrEnum[centerMapping.labelKey as keyof typeof localizeStrEnum]),
    } : null;

    const layout = {
      // Gradient ring configuration
      ring: {
        left: { x: positions.leftRingX, y: positions.centerY },
        right: { x: positions.rightRingX, y: positions.centerY },
        innerRadius: params.ring.innerRadius,
        outerRadius: params.ring.outerRadius,
      },
      
      // LED configuration (dynamically generated from layout)
      leds: {
        left: leftLeds,
        right: rightLeds,
      },
      
      // Center button configuration (ABXY, Guide, or null)
      centerButton,
      
      visual: params.visual,
    };

    // ===== Draw gradient rings =====
    drawGradientRing(ctx, layout.ring.left, layout.ring.innerRadius, layout.ring.outerRadius, 
                     layout.leds.left, colors);
    drawGradientRing(ctx, layout.ring.right, layout.ring.innerRadius, layout.ring.outerRadius, 
                     layout.leds.right, colors);

    // ===== Draw all LEDs =====
    [...layout.leds.left, ...layout.leds.right].forEach(led => {
      const isSelected = led.idx === activeZone;
      drawLED(ctx, led.x, led.y, colors[led.idx], isSelected, led.label, layout.visual, width, params.ledSpacing);
    });

    // ===== Draw Center Button (ABXY, Guide, or none) =====
    if (layout.centerButton) {
      const [cr, cg, cb] = colors[layout.centerButton.idx];
      const isCenterSelected = layout.centerButton.idx === activeZone;
      const centerRadius = isCenterSelected ? layout.visual.led.radiusSelected : layout.visual.led.radius;
      const centerBorderWidth = isCenterSelected ? layout.visual.led.borderWidthSelected : layout.visual.led.borderWidth;
      
      ctx.beginPath();
      ctx.arc(layout.centerButton.x, layout.centerButton.y, centerRadius, 0, Math.PI * 2);
      ctx.fillStyle = `rgb(${cr}, ${cg}, ${cb})`;
      ctx.fill();
      ctx.strokeStyle = isCenterSelected ? LED_SELECTED : LED_NORMAL;
      ctx.lineWidth = centerBorderWidth;
      ctx.stroke();

      // Center button index number inside - auto contrast
      ctx.fillStyle = getContrastColor(cr, cg, cb);
      ctx.font = `${layout.visual.label.fontSizeBold} sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`${layout.centerButton.idx + 1}`, layout.centerButton.x, layout.centerButton.y);
    }
    
    // Center button label below (if exists)
    if (layout.centerButton) {
      ctx.fillStyle = "#B8BCBF";
      ctx.font = `${layout.visual.label.fontSize} sans-serif`;
      ctx.textBaseline = "top";
      const isCenterSelected = layout.centerButton.idx === activeZone;
      const centerLabelOffset = isCenterSelected ? 15 : 13;
      ctx.fillText(layout.centerButton.label, layout.centerButton.x, layout.centerButton.y + centerLabelOffset);
    }
  };

  // Animation loop for playing mode
  useEffect(() => {
    if (!isPlaying) {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = undefined;
      }
      drawPreview(); // Draw static frame
      return;
    }

    // Calculate cycle duration based on speed (0-20) and keyframes
    // Hardware timing: each frame has a duration that depends on speed
    // Total cycle = per-frame duration × number of keyframes
    const minPerFrameDuration = 150;   // milliseconds per frame at max speed (20)
    const maxPerFrameDuration = 3500;  // milliseconds per frame at min speed (0)
    const perFrameDuration = maxPerFrameDuration - ((maxPerFrameDuration - minPerFrameDuration) * speed / 20);
    const cycleDuration = perFrameDuration * keyframes.length;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = (elapsed % cycleDuration) / cycleDuration;

      // Get interpolated and brightness-adjusted colors
      const interpolatedColors = getInterpolatedFrame(progress);
      const finalColors = applyBrightness(interpolatedColors);

      // Draw with interpolated colors, using latest selectedZone from ref
      // 使用 ref 中最新的 selectedZone 绘制插值颜色
      drawPreviewWithColors(finalColors, selectedZoneRef.current);

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    startTimeRef.current = 0;
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, speed, brightness, keyframes]);

  // Static preview when not playing
  useEffect(() => {
    if (!isPlaying) {
      drawPreview();
    }
  }, [keyframes, currentFrame, selectedZone, brightness, isPlaying, layoutConfig]);

  /**
   * Handle canvas click to select zone
   * 处理画布点击以选择区域
   */
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onZoneClick) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Reuse centralized layout calculation with layoutConfig
    const { clickableZones } = calculateLEDLayout(300, 80, layoutConfig);
    
    // Check clicks with 30px hit radius
    for (const led of clickableZones) {
      const dist = Math.sqrt((x - led.x) ** 2 + (y - led.y) ** 2);
      if (dist <= 30) {
        onZoneClick(led.zone);
        return;
      }
    }
  };

  /**
   * Draw gradient ring for a stick
   * 为摇杆绘制渐变环
   */
  const drawGradientRing = (
    ctx: CanvasRenderingContext2D,
    center: { x: number; y: number },
    innerRadius: number,
    outerRadius: number,
    leds: Array<{ x: number; y: number; idx: number }>,
    colors: RGBTuple[]
  ) => {
    // Calculate angles for each LED relative to this ring's center
    const ledsWithAngles = leds.map(led => {
      // Calculate angle from ring center to LED position
      // Note: Canvas Y axis is inverted, so we use (center.y - led.y) for correct angle
      let angle = Math.atan2(center.y - led.y, led.x - center.x);
      
      // Normalize to [0, 2π] range for consistent interpolation
      if (angle < 0) {
        angle += Math.PI * 2;
      }
      
      return {
        angle,
        idx: led.idx
      };
    });

    const segments = 60; // More segments = smoother gradient

    for (let i = 0; i < segments; i++) {
      const startAngle = (i / segments) * Math.PI * 2;
      const endAngle = ((i + 1) / segments) * Math.PI * 2;

      // Calculate color at this angle (interpolate between LEDs)
      const color = getColorAtAngle(startAngle, ledsWithAngles, colors);

      // Draw arc segment - flip angles for Canvas y-axis
      ctx.beginPath();
      ctx.arc(center.x, center.y, outerRadius, -startAngle, -endAngle, true);
      ctx.arc(center.x, center.y, innerRadius, -endAngle, -startAngle, false);
      ctx.closePath();
      ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
      ctx.fill();
    }

    // Draw inner and outer borders
    ctx.beginPath();
    ctx.arc(center.x, center.y, outerRadius, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(center.x, center.y, innerRadius, 0, Math.PI * 2);
    ctx.stroke();
  };

  /**
   * Calculate interpolated color at a specific angle
   * 计算特定角度的插值颜色
   */
  const getColorAtAngle = (
    angle: number,
    leds: Array<{ angle: number; idx: number }>,
    colors: RGBTuple[]
  ): RGBTuple => {
    // Normalize angle to [0, 2π]
    angle = ((angle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);

    // Find nearest two LEDs
    const sortedLEDs = [...leds].sort((a, b) => a.angle - b.angle);

    let led1 = sortedLEDs[sortedLEDs.length - 1];
    let led2 = sortedLEDs[0];

    for (let i = 0; i < sortedLEDs.length; i++) {
      if (sortedLEDs[i].angle > angle) {
        led2 = sortedLEDs[i];
        led1 = sortedLEDs[i - 1] || sortedLEDs[sortedLEDs.length - 1];
        break;
      }
    }

    // Calculate interpolation ratio
    let angle1 = led1.angle;
    let angle2 = led2.angle;

    // Handle wrap around 0°
    if (angle2 < angle1) {
      angle2 += Math.PI * 2;
      if (angle < angle1) {
        angle += Math.PI * 2;
      }
    }

    const t = (angle - angle1) / (angle2 - angle1);

    // RGB interpolation
    const color1 = colors[led1.idx];
    const color2 = colors[led2.idx];

    return [
      Math.round(color1[0] + (color2[0] - color1[0]) * t),
      Math.round(color1[1] + (color2[1] - color1[1]) * t),
      Math.round(color1[2] + (color2[2] - color1[2]) * t),
    ];
  };

  /**
   * Draw a single LED
   * 绘制单个 LED
   */
  const drawLED = (
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    color: RGBTuple,
    isSelected: boolean,
    label: string,
    visualConfig: VisualConfig,
    canvasWidth: number = 300,
    ledSpacing: number = 70
  ) => {
    const [r, g, b] = color;
    const radius = isSelected ? visualConfig.led.radiusSelected : visualConfig.led.radius;
    const borderWidth = isSelected ? visualConfig.led.borderWidthSelected : visualConfig.led.borderWidth;
    const labelDist = isSelected ? visualConfig.label.distanceSelected : visualConfig.label.distance;

    // Draw LED circle
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
    ctx.fill();
    ctx.strokeStyle = isSelected ? LED_SELECTED : LED_NORMAL;
    ctx.lineWidth = borderWidth;
    ctx.stroke();

    // Index number inside LED - auto contrast
    ctx.fillStyle = getContrastColor(r, g, b);
    ctx.font = `${visualConfig.label.fontSizeBold} sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const ledNumber = label.match(/\d+/)?.[0] || "";
    ctx.fillText(ledNumber, x, y);

    // Label position based on LED absolute position in canvas
    ctx.fillStyle = "#B8BCBF";
    ctx.font = `${visualConfig.label.fontSize} sans-serif`;
    
    let labelX = x;
    let labelY = y;
    
    // Determine label direction based on LED position
    const centerX = canvasWidth / 2;
    const quarterPoint = ledSpacing * 0.75;
    
    if (x < centerX - quarterPoint) {
      // Outer left LEDs (L6, L7) - label on the left
      ctx.textAlign = "right";
      labelX = x - labelDist;
      ctx.textBaseline = "middle";
    } else if (x < centerX) {
      // Inner left LEDs (L5, L8) - label on the right
      ctx.textAlign = "left";
      labelX = x + labelDist;
      ctx.textBaseline = "middle";
    } else if (x < centerX + quarterPoint) {
      // Inner right LEDs (R4, R1) - label on the left
      ctx.textAlign = "right";
      labelX = x - labelDist;
      ctx.textBaseline = "middle";
    } else {
      // Outer right LEDs (R3, R2) - label on the right
      ctx.textAlign = "left";
      labelX = x + labelDist;
      ctx.textBaseline = "middle";
    }
    
    ctx.fillText(label, labelX, labelY);
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleCanvasClick}
      style={{
        width: "300px",
        height: "80px",
        backgroundColor: "transparent",
        border: "none",
        borderRadius: "0px",
        cursor: onZoneClick ? "pointer" : "default"
      }}
    />
  );
};
