// MSI LED Preview Component
// MSI LED 预览组件

import { FC, useEffect, useRef } from "react";
import { RGBTuple } from "../types/msiCustomRgb";

interface MsiLEDPreviewProps {
  keyframes: RGBTuple[][];
  currentFrame: number;
  selectedZone: number | null;
  onZoneClick?: (zone: number) => void;
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
 * Calculate LED layout positions and parameters
 * 计算 LED 布局位置和参数
 */
const calculateLEDLayout = (width: number, height: number) => {
  const params = {
    canvas: { width, height },
    padding: { left: 40, right: 40, top: 10, bottom: 10 },
    ledSpacing: 70,
    ring: { innerRadius: 20, outerRadius: 28, offsetFromEdge: 35 },
    visual: {
      led: { radius: 6, radiusSelected: 8, borderWidth: 1, borderWidthSelected: 2 },
      label: { distance: 10, distanceSelected: 12, fontSize: "6px", fontSizeBold: "bold 6px" },
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
    // All clickable LED zones
    clickableZones: [
      { x: leftLedLeft, y: ledTop, zone: 5 },       // L6
      { x: leftLedRight, y: ledTop, zone: 4 },      // L5
      { x: leftLedLeft, y: ledBottom, zone: 6 },    // L7
      { x: leftLedRight, y: ledBottom, zone: 7 },   // L8
      { x: rightLedLeft, y: ledTop, zone: 3 },      // R4
      { x: rightLedRight, y: ledTop, zone: 2 },     // R3
      { x: rightLedLeft, y: ledBottom, zone: 0 },   // R1
      { x: rightLedRight, y: ledBottom, zone: 1 },  // R2
      { x: width / 2, y: centerY, zone: 8 },        // ABXY
    ],
  };
};

export const MsiLEDPreview: FC<MsiLEDPreviewProps> = ({
  keyframes,
  currentFrame,
  selectedZone,
  onZoneClick
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawPreview();
  }, [keyframes, currentFrame, selectedZone]);

  const drawPreview = () => {
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

    const colors = keyframes[currentFrame];

    // Get layout from centralized calculation
    const { params, positions } = calculateLEDLayout(width, height);

    const layout = {
      // Gradient ring configuration
      ring: {
        left: { x: positions.leftRingX, y: positions.centerY },
        right: { x: positions.rightRingX, y: positions.centerY },
        innerRadius: params.ring.innerRadius,
        outerRadius: params.ring.outerRadius,
      },
      
      // LED configuration
      leds: {
        left: [
          { x: positions.leftLedLeft, y: positions.ledTop, idx: 5, label: "L6" },
          { x: positions.leftLedRight, y: positions.ledTop, idx: 4, label: "L5" },
          { x: positions.leftLedLeft, y: positions.ledBottom, idx: 6, label: "L7" },
          { x: positions.leftLedRight, y: positions.ledBottom, idx: 7, label: "L8" },
        ],
        right: [
          { x: positions.rightLedLeft, y: positions.ledTop, idx: 3, label: "R4" },
          { x: positions.rightLedRight, y: positions.ledTop, idx: 2, label: "R3" },
          { x: positions.rightLedLeft, y: positions.ledBottom, idx: 0, label: "R1" },
          { x: positions.rightLedRight, y: positions.ledBottom, idx: 1, label: "R2" },
        ],
      },
      
      // ABXY configuration
      abxy: {
        x: width / 2,
        y: positions.centerY,
        idx: 8,
        label: "ABXY",
      },
      
      visual: params.visual,
    };

    // ===== Draw gradient rings =====
    drawGradientRing(ctx, layout.ring.left, layout.ring.innerRadius, layout.ring.outerRadius, 
                     layout.leds.left, colors);
    drawGradientRing(ctx, layout.ring.right, layout.ring.innerRadius, layout.ring.outerRadius, 
                     layout.leds.right, colors);

    // ===== Draw all LEDs =====
    [...layout.leds.left, ...layout.leds.right].forEach(led => {
      const isSelected = led.idx === selectedZone;
      drawLED(ctx, led.x, led.y, colors[led.idx], isSelected, led.label, layout.visual, width, params.ledSpacing);
    });

    // ===== Draw ABXY =====
    const [ar, ag, ab] = colors[layout.abxy.idx];
    const isAbxySelected = layout.abxy.idx === selectedZone;
    const abxyRadius = isAbxySelected ? layout.visual.led.radiusSelected : layout.visual.led.radius;
    const abxyBorderWidth = isAbxySelected ? layout.visual.led.borderWidthSelected : layout.visual.led.borderWidth;
    
    ctx.beginPath();
    ctx.arc(layout.abxy.x, layout.abxy.y, abxyRadius, 0, Math.PI * 2);
    ctx.fillStyle = `rgb(${ar}, ${ag}, ${ab})`;
    ctx.fill();
    ctx.strokeStyle = isAbxySelected ? LED_SELECTED : LED_NORMAL;
    ctx.lineWidth = abxyBorderWidth;
    ctx.stroke();

    // ABXY index number inside - auto contrast
    ctx.fillStyle = getContrastColor(ar, ag, ab);
    ctx.font = `${layout.visual.label.fontSizeBold} sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("9", layout.abxy.x, layout.abxy.y);
    
    // ABXY label below
    ctx.fillStyle = "#B8BCBF";
    ctx.font = `${layout.visual.label.fontSize} sans-serif`;
    ctx.textBaseline = "top";
    const abxyLabelOffset = isAbxySelected ? 15 : 13;
    ctx.fillText(layout.abxy.label, layout.abxy.x, layout.abxy.y + abxyLabelOffset);
  };

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
    
    // Reuse centralized layout calculation
    const { clickableZones } = calculateLEDLayout(300, 80);
    
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
