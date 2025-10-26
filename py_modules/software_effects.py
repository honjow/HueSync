import math
import threading
import time
from typing import Callable, Optional

from config import logger, SOFTWARE_EFFECT_UPDATE_RATE
from utils import Color, get_battery_info


def hsv_to_rgb(h: float, s: float, v: float) -> Color:
    """
    将 HSV 颜色转换为 RGB 颜色

    Args:
        h: 色相 (0-360)
        s: 饱和度 (0-1)
        v: 明度 (0-1)

    Returns:
        Color: RGB颜色
    """
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return Color(int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


class SoftwareEffect:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if not self._running:
                self._running = True
                self._thread = threading.Thread(target=self._run)
                self._thread.daemon = True
                self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False
            if self._thread:
                self._thread.join()
                self._thread = None

    def _run(self):
        pass


class PulseEffect(SoftwareEffect):
    def __init__(
        self,
        base_color: Color,
        set_color_callback: Callable[[Color], None],
        speed: float = 0.6,
        hold_time: float = 1.0,
        update_rate: float = SOFTWARE_EFFECT_UPDATE_RATE,  # Update rate | 更新频率
    ):
        """
        初始化呼吸灯效果

        Args:
            base_color (Color): 基础颜色
            set_color_callback: 设置颜色的回调函数
            speed (float): 呼吸速度，默认为0.25
                         1.0 表示大约2.5秒一个周期
                         0.25 表示大约10秒一个周期
            hold_time (float): 在最大和最小亮度处的维持时间（秒）
            update_rate (float): 更新频率（Hz）
        """
        super().__init__()
        self.base_color = base_color
        self.set_color_callback = set_color_callback
        self.speed = speed
        self.hold_time = hold_time
        self.update_rate = update_rate
        self._brightness = 1.0

    def _apply_brightness(self, color: Color, brightness: float) -> Color:
        """Apply brightness value to color"""
        return Color(
            int(color.R * brightness),
            int(color.G * brightness),
            int(color.B * brightness),
        )

    def _run(self):
        """Run breathing light effect"""
        sleep_time = 1.0 / self.update_rate
        state = "up"  # State: up(rising), hold_high(hold max), down(falling), hold_low(hold min) | 状态：up（上升），hold_high（保持最大），down（下降），hold_low（保持最小）
        hold_end = 0
        phase = 0

        while self._running:
            current_time = time.time()

            if state == "up":
                # Rising phase | 上升阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness > 0.99:  # Reached maximum value | 达到最大值
                    state = "hold_high"
                    hold_end = current_time + self.hold_time
                    brightness = 1.0
                    logger.debug("Entering maximum value hold state")

            elif state == "hold_high":
                # Hold maximum value | 保持最大值
                brightness = 1.0
                if current_time >= hold_end:
                    state = "down"
                    phase = math.pi / 2  # Start falling from maximum | 从最大值开始下降
                    logger.debug("Starting brightness down phase")

            elif state == "down":
                # Falling phase | 下降阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness < 0.01:  # Reached minimum value | 达到最小值
                    state = "hold_low"
                    hold_end = current_time + self.hold_time
                    brightness = 0.0
                    logger.debug("Entering minimum value hold state")

            else:  # hold_low
                # Hold minimum value | 保持最小值
                brightness = 0.0
                if current_time >= hold_end:
                    state = "up"
                    phase = (
                        3 * math.pi / 2
                    )  # Start rising from minimum | 从最小值开始上升
                    logger.debug("Starting brightness up phase")

            # Apply brightness to color | 应用亮度到颜色
            current_color = self._apply_brightness(self.base_color, brightness)
            self.set_color_callback(current_color)
            time.sleep(sleep_time)


class RainbowEffect(SoftwareEffect):
    def __init__(
        self,
        set_color_callback: Callable[[Color], None],
        speed: float = 1.0,
        update_rate: float = SOFTWARE_EFFECT_UPDATE_RATE,  # Update rate | 更新频率
    ):
        """
        初始化彩虹灯效果

        Args:
            set_color_callback: 设置颜色的回调函数
            speed (float): 彩虹变化速度，默认为1.0
                         1.0 表示每秒转动30度色相
                         0.2 表示每秒转动6度色相
        """
        super().__init__()
        self.set_color_callback = set_color_callback
        self.speed = speed
        self._hue = 0.0
        self.update_rate = update_rate

    def _run(self):
        """Run rainbow light effect"""
        start_time = time.time()
        while self._running:
            self.sleep_time = 1.0 / self.update_rate
            # Calculate current hue | 计算当前色相
            current_time = time.time() - start_time
            hue = (
                current_time * 30 * self.speed
            ) % 360  # 30 degrees per second * speed | 每秒转30度 * speed

            # Convert to RGB color | 转换为RGB颜色
            current_color = hsv_to_rgb(hue, 1.0, 1.0)

            # Call callback to set color | 调用回调函数设置颜色
            self.set_color_callback(current_color)

            # Control update rate | 控制更新频率
            time.sleep(self.sleep_time)


class GradientEffect(SoftwareEffect):
    """
    Dual-color gradient transition effect
    双色渐变过渡效果
    
    Smoothly transitions between two colors in a continuous cycle.
    在两个颜色之间平滑循环渐变。
    """
    
    def __init__(
        self,
        color1: Color,
        color2: Color,
        set_color_callback: Callable[[Color], None],
        speed: float = 0.2,
        transition: str = "sine",
        update_rate: float = SOFTWARE_EFFECT_UPDATE_RATE,  # Update rate | 更新频率
    ):
        """
        初始化双色渐变过渡效果

        Args:
            color1: 第一个颜色
            color2: 第二个颜色
            set_color_callback: 设置颜色的回调函数
            speed: 过渡速度，默认为 0.5
                  1.0 表示每秒完成一次完整的过渡
                  0.5 表示每2秒完成一次完整的过渡
            transition: 过渡模式，可选值：
                      - "sine": 正弦过渡，更平滑
                      - "linear": 线性过渡，匀速
                      - "ease": 缓动过渡，在两端较慢，中间较快
        """
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.set_color_callback = set_color_callback
        self.speed = speed
        self.transition = transition
        self.update_rate = update_rate

    def _interpolate_color(self, color1: Color, color2: Color, t: float) -> Color:
        """Interpolate between two colors"""

        def lerp(a: int, b: int, t: float) -> int:
            return int(a + (b - a) * t)

        return Color(
            lerp(color1.R, color2.R, t),
            lerp(color1.G, color2.G, t),
            lerp(color1.B, color2.B, t),
        )

    def _get_transition_value(self, t: float) -> float:
        """
        Calculate transition value based on transition mode
        根据过渡模式计算过渡值
        """
        t = t % 1.0  # Ensure t is in [0, 1] range | 确保 t 在 [0, 1] 范围内

        match self.transition:
            case "sine":
                # Use sine function for smooth transition | 使用正弦函数实现平滑过渡
                return (math.sin(t * math.pi * 2 - math.pi / 2) + 1) / 2
            case "linear":
                # Linear transition | 线性过渡
                return t
            case "ease":
                # Ease transition using cubic curve | 缓动过渡（使用三次方曲线）
                return 3 * t * t - 2 * t * t * t
            case _:
                return t

    def _run(self):
        """
        Run dual-color transition effect
        运行双色过渡效果
        """
        start_time = time.time()
        while self._running:
            self.sleep_time = 1.0 / self.update_rate
            # Calculate transition progress at current time | 计算当前时间点的过渡进度
            current_time = time.time() - start_time
            progress = (current_time * self.speed) % 1.0

            # Apply transition function | 应用过渡函数
            t = self._get_transition_value(progress)

            # Calculate current color | 计算当前颜色
            current_color = self._interpolate_color(self.color1, self.color2, t)

            # Set color | 设置颜色
            self.set_color_callback(current_color)

            # Control update rate | 控制更新频率
            time.sleep(
                self.sleep_time
            )  # According to configured update rate | 根据设置的更新频率


class DualityEffect(SoftwareEffect):
    """
    Dual-color alternating pulse effect
    双色交替呼吸效果
    
    Alternates between two colors with breathing animation.
    两个颜色交替进行呼吸动画。
    
    Cycle: Color1 (dark→bright→dark) → Color2 (dark→bright→dark) → repeat
    周期：颜色1（暗→亮→暗）→ 颜色2（暗→亮→暗）→ 重复
    """
    
    def __init__(
        self,
        color1: Color,
        color2: Color,
        set_color_callback: Callable[[Color], None],
        speed: float = 0.6,
        hold_time: float = 0.5,
        switch_delay: float = 0.2,
        update_rate: float = SOFTWARE_EFFECT_UPDATE_RATE,
    ):
        """
        初始化双色交替呼吸效果

        Args:
            color1: 第一个颜色
            color2: 第二个颜色
            set_color_callback: 设置颜色的回调函数
            speed: 呼吸速度，默认为 0.6
                  1.0 表示每秒约2.5个周期
                  0.6 表示每秒约1.5个周期
            hold_time: 在最亮和最暗处停留的时间（秒）
            switch_delay: 两个颜色之间切换的延迟时间（秒）
            update_rate: 更新频率（Hz）
        """
        super().__init__()
        self.color1 = color1
        self.color2 = color2
        self.set_color_callback = set_color_callback
        self.speed = speed
        self.hold_time = hold_time
        self.switch_delay = switch_delay
        self.update_rate = update_rate
        self._current_color_index = 0  # 0 for color1, 1 for color2

    def _apply_brightness(self, color: Color, brightness: float) -> Color:
        """Apply brightness value to color"""
        return Color(
            int(color.R * brightness),
            int(color.G * brightness),
            int(color.B * brightness),
        )

    def _pulse_once(self, color: Color) -> None:
        """
        Perform one complete pulse cycle for a single color
        对单个颜色执行一次完整的呼吸周期
        
        Cycle: dark(0%) → bright(100%) → hold → dark(0%) → hold
        周期: 暗(0%) → 亮(100%) → 停留 → 暗(0%) → 停留
        """
        sleep_time = 1.0 / self.update_rate
        state = "up"  # State: up(rising), hold_high, down(falling), hold_low
        hold_end = 0
        phase = 3 * math.pi / 2  # Start from minimum (dark)
        
        while self._running and state != "done":
            current_time = time.time()
            
            if state == "up":
                # Rising phase | 上升阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness > 0.99:  # Reached maximum
                    state = "hold_high"
                    hold_end = current_time + self.hold_time
                    brightness = 1.0
                    
            elif state == "hold_high":
                # Hold at maximum brightness | 保持最大亮度
                brightness = 1.0
                if current_time >= hold_end:
                    state = "down"
                    phase = math.pi / 2  # Start falling from maximum
                    
            elif state == "down":
                # Falling phase | 下降阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness < 0.01:  # Reached minimum
                    state = "hold_low"
                    hold_end = current_time + self.hold_time
                    brightness = 0.0
                    
            elif state == "hold_low":
                # Hold at minimum brightness | 保持最小亮度
                brightness = 0.0
                if current_time >= hold_end:
                    state = "done"
                    brightness = 0.0
            
            # Apply brightness to color and set | 应用亮度并设置颜色
            current_color = self._apply_brightness(color, brightness)
            self.set_color_callback(current_color)
            time.sleep(sleep_time)

    def _run(self):
        """
        Run dual-color alternating pulse effect
        运行双色交替呼吸效果
        """
        while self._running:
            # Pulse color1 | 颜色1呼吸
            self._pulse_once(self.color1)
            
            if not self._running:
                break
                
            # Delay between color switches | 颜色切换延迟
            if self.switch_delay > 0:
                time.sleep(self.switch_delay)
            
            if not self._running:
                break
            
            # Pulse color2 | 颜色2呼吸
            self._pulse_once(self.color2)
            
            if not self._running:
                break
                
            # Delay before repeating | 重复前的延迟
            if self.switch_delay > 0:
                time.sleep(self.switch_delay)


class BatteryEffect(SoftwareEffect):
    """
    Battery status light effect, displays different colors based on battery level and charging status
    电池状态灯效，根据电池电量和充电状态显示不同颜色
    """

    def __init__(
        self,
        set_color_callback: Callable[[Color], None],
        update_rate: float = 0.5,  # Update rate | 更新频率
        low_battery_threshold: int = 20,  # Low battery threshold | 低电量阈值
        mid_battery_threshold: int = 50,  # Mid battery threshold | 中等电量阈值
        high_battery_threshold: int = 90,  # High battery threshold | 高电量阈值
        low_color: Color = Color(255, 0, 0),  # Low battery color | 低电量颜色 红色
        mid_color: Color = Color(
            255, 70, 0
        ),  # Mid low battery color | 中低电量颜色 橙色
        high_color: Color = Color(0, 0, 255),  # High battery color | 高电量颜色 蓝色
        is_charging_color: Color = Color(0, 255, 0),  # Charging color | 充电颜色 绿色
        base_brightness: int = 100,  # Base brightness | 基础亮度 0 - 100
    ):
        """
        初始化电池状态灯效

        Args:
            set_color_callback: 设置颜色的回调函数
            update_rate (float): 更新频率（Hz）
            low_battery_threshold (int): 低电量阈值（0-100）
            mid_battery_threshold (int): 中等电量阈值（0-100）
            high_battery_threshold (int): 高电量阈值（0-100）
            base_brightness (int): 基础亮度（0-100）
        """
        super().__init__()
        self.set_color_callback = set_color_callback
        self.update_rate = update_rate
        self.low_battery_threshold = low_battery_threshold
        self.mid_battery_threshold = mid_battery_threshold
        self.high_battery_threshold = high_battery_threshold
        self.low_color = low_color
        self.mid_color = mid_color
        self.high_color = high_color
        self.is_charging_color = is_charging_color

        self.base_brightness = max(0, min(100, base_brightness))
        self.sleep_time = 1.0 / self.update_rate
        self.latest_color = Color(0, 0, 0)
        self._breathing_speed = (
            0.25  # Breathing effect frequency (Hz) | 呼吸效果频率 (Hz)
        )
        self._breathing_update_rate = (
            SOFTWARE_EFFECT_UPDATE_RATE  # Breathing effect update rate (Hz) | 呼吸效果更新频率 (Hz)
        )

    def _get_battery_color(self, percentage: int, is_charging: bool) -> Color:
        """
        Return corresponding color based on battery status
        根据电池状态返回对应的颜色
        """
        if is_charging:
            # Charging | 充电中
            return self.is_charging_color
        elif percentage < 0:
            # Cannot get battery level: black | 无法获取电量：黑色
            return Color(0, 0, 0)
        elif percentage <= self.low_battery_threshold:
            # Low battery | 低电量
            return self.low_color
        elif percentage <= self.mid_battery_threshold:
            # Medium battery | 中等电量
            return self.mid_color
        elif percentage <= self.high_battery_threshold:
            # High battery | 较高电量
            return self.high_color
        else:
            # Full battery | 高电量
            return self.is_charging_color

    def _apply_brightness(self, color: Color, brightness: float) -> Color:
        """
        Apply brightness value to color
        应用亮度值到颜色
        """
        return Color(
            int(color.R * brightness),
            int(color.G * brightness),
            int(color.B * brightness),
        )

    def _run(self):
        """
        Run battery status light effect
        运行电池状态灯效
        """
        sleep_time = 1.0 / self.update_rate
        breathing_sleep_time = 1.0 / self._breathing_update_rate

        while self._running:
            # Get battery info | 获取电池信息
            percentage, is_charging = get_battery_info()

            # Set color based on status | 根据状态设置颜色
            color = self._get_battery_color(percentage, is_charging)
            logger.debug(
                f"Battery color: {color}, base brightness: {self.base_brightness}"
            )

            # Apply base brightness (convert to 0-1 range) | 应用基础亮度（转换为 0-1 范围）
            brightness_factor = self.base_brightness / 100.0

            # Add breathing effect if charging | 如果正在充电，添加呼吸效果
            if is_charging:
                # Use current time to create simple breathing effect | 使用当前时间来创建简单的呼吸效果
                phase = (time.time() * self._breathing_speed * 2 * math.pi) % (
                    2 * math.pi
                )
                # sin value range from -1 to 1, convert to 0 to 1 | sin 值范围从 -1 到 1，转换到 0 到 1
                normalized = (math.sin(phase) + 1) / 2
                # Map 0-1 range to 0.01-1.0 and multiply with base brightness | 将 0-1 的范围映射到 0.01-1.0，并与基础亮度相乘
                brightness = (normalized * 0.99 + 0.01) * brightness_factor
            else:
                brightness = brightness_factor

            # Apply brightness | 应用亮度
            color = self._apply_brightness(color, brightness)
            logger.debug(f"Battery color (adjusted): {color}")

            # Only set when color changes | 只有当颜色发生变化时才设置
            if self.latest_color != color:
                self.set_color_callback(color)
                self.latest_color = color

            # Wait for next update | 等待下一次更新
            if is_charging:
                time.sleep(
                    breathing_sleep_time
                )  # Use shorter interval for breathing effect | 呼吸效果时使用较短的间隔
            else:
                time.sleep(
                    sleep_time
                )  # Use normal interval for non-breathing effect | 非呼吸效果时使用正常间隔
