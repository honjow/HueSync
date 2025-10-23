// MSI LED Preview Component
// MSI LED 预览组件

import { FC, useEffect, useRef } from "react";
import { RGBTuple } from "../types/msiCustomRgb";

interface MsiLEDPreviewProps {
  keyframes: RGBTuple[][];
  currentFrame: number;
  selectedZone: number | null;
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

export const MsiLEDPreview: FC<MsiLEDPreviewProps> = ({
  keyframes,
  currentFrame,
  selectedZone
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

    // ===== Base Parameters =====
    // Define all base parameters for calculation
    const params = {
      canvas: {
        width,   // 300
        height,  // 80
      },
      padding: {
        left: 40,      // Distance from left edge to first LED
        right: 40,     // Distance from right edge to last LED
        top: 10,       // Distance from top edge to top LEDs
        bottom: 10,    // Distance from bottom edge to bottom LEDs
      },
      ledSpacing: 70,  // Horizontal spacing between LEDs in same group
      groupSpacing: 80, // Horizontal spacing between left and right groups
      ring: {
        innerRadius: 20,
        outerRadius: 28,
        offsetFromEdge: 35,  // Distance from edge to ring center
      },
      visual: {
        led: {
          radius: 6,
          radiusSelected: 8,
          borderWidth: 1,
          borderWidthSelected: 2,
        },
        label: {
          distance: 10,
          distanceSelected: 12,
          fontSize: "6px",
          fontSizeBold: "bold 6px",
        },
      },
    };

    // ===== Calculate Layout from Parameters =====
    // All positions are calculated from base parameters
    const centerY = params.canvas.height / 2;
    
    // Calculate LED positions
    const leftLedLeft = params.padding.left;
    const leftLedRight = leftLedLeft + params.ledSpacing;
    const rightLedLeft = params.canvas.width - params.padding.right - params.ledSpacing;
    const rightLedRight = params.canvas.width - params.padding.right;
    const ledTop = params.padding.top;
    const ledBottom = params.canvas.height - params.padding.bottom;
    
    // Calculate ring centers
    const leftRingX = params.padding.left + params.ring.offsetFromEdge;
    const rightRingX = params.canvas.width - params.padding.right - params.ring.offsetFromEdge;

    const layout = {
      // Gradient ring configuration
      ring: {
        left: { x: leftRingX, y: centerY },
        right: { x: rightRingX, y: centerY },
        innerRadius: params.ring.innerRadius,
        outerRadius: params.ring.outerRadius,
      },
      
      // LED configuration - calculated from parameters
      leds: {
        // Left stick LEDs
        left: [
          { x: leftLedLeft, y: ledTop, idx: 5, label: "L6" },       // Top-left
          { x: leftLedRight, y: ledTop, idx: 4, label: "L5" },      // Top-right
          { x: leftLedLeft, y: ledBottom, idx: 6, label: "L7" },    // Bottom-left
          { x: leftLedRight, y: ledBottom, idx: 7, label: "L8" },   // Bottom-right
        ],
        // Right stick LEDs
        right: [
          { x: rightLedLeft, y: ledTop, idx: 3, label: "R4" },      // Top-left
          { x: rightLedRight, y: ledTop, idx: 2, label: "R3" },     // Top-right
          { x: rightLedLeft, y: ledBottom, idx: 0, label: "R1" },   // Bottom-left
          { x: rightLedRight, y: ledBottom, idx: 1, label: "R2" },  // Bottom-right
        ],
      },
      
      // ABXY configuration (center of canvas)
      abxy: {
        x: params.canvas.width / 2,
        y: centerY,
        idx: 8,
        label: "ABXY",
      },
      
      // Visual parameters
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

    // ABXY index number inside
    ctx.fillStyle = "#FFFFFF";
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

    // Draw inner and outer borders (optional)
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

    // Index number inside LED
    ctx.fillStyle = "#FFFFFF";
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
    // Four zones: outer left, inner left, inner right, outer right
    const centerX = canvasWidth / 2;
    const quarterPoint = ledSpacing * 0.75; // Threshold for inner/outer detection
    
    if (x < centerX - quarterPoint) {
      // Outer left LEDs (L6, L7) - label on the left (outside)
      ctx.textAlign = "right";
      labelX = x - labelDist;
      ctx.textBaseline = "middle";
    } else if (x < centerX) {
      // Inner left LEDs (L5, L8) - label on the right (inside)
      ctx.textAlign = "left";
      labelX = x + labelDist;
      ctx.textBaseline = "middle";
    } else if (x < centerX + quarterPoint) {
      // Inner right LEDs (R4, R1) - label on the left (inside)
      ctx.textAlign = "right";
      labelX = x - labelDist;
      ctx.textBaseline = "middle";
    } else {
      // Outer right LEDs (R3, R2) - label on the right (outside)
      ctx.textAlign = "left";
      labelX = x + labelDist;
      ctx.textBaseline = "middle";
    }
    
    ctx.fillText(label, labelX, labelY);
  };

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: "300px",
        height: "80px",
        backgroundColor: "transparent",
        border: "none",
        borderRadius: "0px"
      }}
    />
  );
};
