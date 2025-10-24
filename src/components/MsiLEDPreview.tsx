// Multi-Zone LED Preview Component
// 多区域 LED 预览组件
// Supports MSI Claw, AyaNeo, and other multi-zone LED devices

import { FC, useEffect, useRef } from "react";
import { RGBTuple } from "../types/customRgb";
import { LEDLayoutConfig } from "../types/ledLayout";
import { MSI_CLAW_LAYOUT } from "../util/ledLayouts";

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
 * Convert polar coordinates to Cartesian coordinates
 * 将极坐标转换为直角坐标
 * @param centerX Center X coordinate
 * @param centerY Center Y coordinate
 * @param radius Radius from center
 * @param angleInDegrees Angle in degrees (0=right, 90=top, 180=left, 270=bottom)
 * @returns Cartesian coordinates {x, y}
 */
const polarToCartesian = (
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
): { x: number; y: number } => {
  // Convert to standard math convention (0° is right, counter-clockwise)
  // Subtract 90 to adjust for canvas coordinate system (0° should be right, not up)
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  };
};

/**
 * Calculate label position and text alignment based on position type
 * 根据位置类型计算标签位置和文本对齐方式
 */
const getLabelPosition = (
  ledX: number,
  ledY: number,
  position: "top" | "bottom" | "left" | "right",
  distance: number = 12
): {
  x: number;
  y: number;
  align: CanvasTextAlign;
  baseline: CanvasTextBaseline;
} => {
  switch (position) {
    case "top":
      return {
        x: ledX,
        y: ledY - distance,
        align: "center",
        baseline: "bottom",
      };
    case "bottom":
      return {
        x: ledX,
        y: ledY + distance,
        align: "center",
        baseline: "top",
      };
    case "left":
      return {
        x: ledX - distance,
        y: ledY,
        align: "right",
        baseline: "middle",
      };
    case "right":
      return {
        x: ledX + distance,
        y: ledY,
        align: "left",
        baseline: "middle",
      };
  }
};

/**
 * Calculate LED layout positions and parameters based on circular coordinates
 * 根据圆形坐标系统计算 LED 位置和参数
 */
const calculateLEDLayout = (width: number, height: number, layoutConfig: LEDLayoutConfig) => {
  // Use visual parameters from layout config, or fallback to defaults
  // 使用布局配置中的视觉参数，或使用默认值
  const params = {
    canvas: { width, height },
    ring: { 
      innerRadius: layoutConfig.visual?.ring?.innerRadius ?? 20,
      outerRadius: layoutConfig.visual?.ring?.outerRadius ?? 28
    },
    visual: {
      led: { 
        radius: layoutConfig.visual?.led?.radius ?? 8,
        radiusSelected: layoutConfig.visual?.led?.radiusSelected ?? 10,
        borderWidth: layoutConfig.visual?.led?.borderWidth ?? 1,
        borderWidthSelected: layoutConfig.visual?.led?.borderWidthSelected ?? 2
      },
      label: { 
        distance: layoutConfig.visual?.label?.distance ?? 10,
        distanceSelected: layoutConfig.visual?.label?.distanceSelected ?? 12,
        fontSize: layoutConfig.visual?.label?.fontSize ?? "8px",
        fontSizeBold: layoutConfig.visual?.label?.fontSizeBold ?? "bold 8px"
      },
    },
  };

  // Calculate LED positions using circular coordinates from layout config
  const ledPositions = layoutConfig.zoneMappings.map(mapping => {
    const center = layoutConfig.circles[mapping.circle];
    if (!center) {
      throw new Error(`Circle center not found for: ${mapping.circle}`);
    }
    const pos = polarToCartesian(center.x, center.y, mapping.radius, mapping.angle);
    return {
      ...pos,
      arrayIndex: mapping.arrayIndex,
      circle: mapping.circle,
      mapping,
    };
  });

  // Separate LEDs by circle for gradient ring drawing
  const leftStickLeds = ledPositions.filter(led => led.circle === "leftStick");
  const rightStickLeds = ledPositions.filter(led => led.circle === "rightStick");

  return {
    params,
    circles: layoutConfig.circles,
    ledPositions,
    leftStickLeds,
    rightStickLeds,
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
   * Draw preview with specific colors using circular layout
   * 使用圆形布局和特定颜色绘制预览
   */
  const drawPreviewWithColors = (colors: RGBTuple[], highlightZone: number | null = null) => {
    // Use provided highlightZone or fall back to selectedZone
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

    // Get layout using circular coordinates
    const { params, circles, ledPositions, leftStickLeds, rightStickLeds } = 
      calculateLEDLayout(width, height, layoutConfig);

    // ===== Draw gradient rings for sticks =====
    if (leftStickLeds.length > 0) {
      const leftLedsForGradient = leftStickLeds.map(led => ({
        x: led.x,
        y: led.y,
        idx: led.arrayIndex,
        label: led.mapping.label.text,
      }));
      drawGradientRing(
        ctx,
        circles.leftStick,
        params.ring.innerRadius,
        params.ring.outerRadius,
        leftLedsForGradient,
        colors
      );
    }

    if (rightStickLeds.length > 0) {
      const rightLedsForGradient = rightStickLeds.map(led => ({
        x: led.x,
        y: led.y,
        idx: led.arrayIndex,
        label: led.mapping.label.text,
      }));
      drawGradientRing(
        ctx,
        circles.rightStick,
        params.ring.innerRadius,
        params.ring.outerRadius,
        rightLedsForGradient,
        colors
      );
    }

    // ===== Draw all LEDs =====
    ledPositions.forEach(led => {
      const isSelected = led.arrayIndex === activeZone;
      const color = colors[led.arrayIndex];
      const [r, g, b] = color;
      
      // Draw LED circle
      const radius = isSelected ? params.visual.led.radiusSelected : params.visual.led.radius;
      const borderWidth = isSelected ? params.visual.led.borderWidthSelected : params.visual.led.borderWidth;
      
      ctx.beginPath();
      ctx.arc(led.x, led.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
      ctx.fill();
      ctx.strokeStyle = isSelected ? LED_SELECTED : LED_NORMAL;
      ctx.lineWidth = borderWidth;
      ctx.stroke();

      // LED index number inside (auto contrast)
      ctx.fillStyle = getContrastColor(r, g, b);
      ctx.font = `${params.visual.label.fontSizeBold} sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const ledNumber = led.mapping.label.text.match(/\d+/)?.[0] || "";
      ctx.fillText(ledNumber, led.x, led.y);

      // LED label outside
      const labelDistance = led.mapping.label.distance || (isSelected ? params.visual.label.distanceSelected : params.visual.label.distance);
      const labelPos = getLabelPosition(led.x, led.y, led.mapping.label.position, labelDistance);
      
      ctx.fillStyle = "#B8BCBF";
      ctx.font = `${params.visual.label.fontSize} sans-serif`;
      ctx.textAlign = labelPos.align;
      ctx.textBaseline = labelPos.baseline;
      ctx.fillText(led.mapping.label.text, labelPos.x, labelPos.y);
    });
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
   * Handle canvas click to select zone using circular coordinates
   * 使用圆形坐标处理画布点击以选择区域
   */
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onZoneClick) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Get LED positions from circular layout
    const { ledPositions } = calculateLEDLayout(300, 80, layoutConfig);
    
    // Check clicks with 30px hit radius
    for (const led of ledPositions) {
      const dist = Math.sqrt((x - led.x) ** 2 + (y - led.y) ** 2);
      if (dist <= 30) {
        onZoneClick(led.arrayIndex);
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
