import math
import threading
import time
from typing import Optional, Callable

from utils import Color
from config import logger


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
        speed: float = 0.25,
        hold_time: float = 2.0,
        update_rate: float = 20.0,  # 更新频率，默认20Hz
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
            update_rate (float): 更新频率（Hz），默认20Hz
        """
        super().__init__()
        self.base_color = base_color
        self.set_color_callback = set_color_callback
        self.speed = speed
        self.hold_time = hold_time
        self.update_rate = update_rate
        self._brightness = 1.0

    def _apply_brightness(self, color: Color, brightness: float) -> Color:
        """应用亮度值到颜色"""
        return Color(
            int(color.R * brightness),
            int(color.G * brightness),
            int(color.B * brightness),
        )

    def _run(self):
        """运行呼吸灯效果"""
        sleep_time = 1.0 / self.update_rate
        state = "up"  # 状态：up（上升），hold_high（保持最大），down（下降），hold_low（保持最小）
        hold_end = 0
        phase = 0

        while self._running:
            current_time = time.time()
            
            if state == "up":
                # 上升阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness > 0.99:  # 达到最大值
                    state = "hold_high"
                    hold_end = current_time + self.hold_time
                    brightness = 1.0
                    logger.debug("进入最大值保持")
            
            elif state == "hold_high":
                # 保持最大值
                brightness = 1.0
                if current_time >= hold_end:
                    state = "down"
                    phase = math.pi/2  # 从最大值开始下降
                    logger.debug("开始下降")
            
            elif state == "down":
                # 下降阶段
                phase = (phase + self.speed * math.pi * sleep_time) % (2 * math.pi)
                brightness = (math.sin(phase) + 1) / 2
                if brightness < 0.01:  # 达到最小值
                    state = "hold_low"
                    hold_end = current_time + self.hold_time
                    brightness = 0.0
                    logger.debug("进入最小值保持")
            
            else:  # hold_low
                # 保持最小值
                brightness = 0.0
                if current_time >= hold_end:
                    state = "up"
                    phase = 3*math.pi/2  # 从最小值开始上升
                    logger.debug("开始上升")

            # 应用亮度到颜色
            current_color = self._apply_brightness(self.base_color, brightness)
            self.set_color_callback(current_color)
            time.sleep(sleep_time)


class RainbowEffect(SoftwareEffect):
    def __init__(
        self,
        set_color_callback: Callable[[Color], None],
        speed: float = 1.0,
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

    def _run(self):
        """运行彩虹灯效果"""
        start_time = time.time()
        while self._running:
            # 计算当前色相
            current_time = time.time() - start_time
            hue = (current_time * 30 * self.speed) % 360  # 每秒转30度 * speed

            # 转换为RGB颜色
            current_color = hsv_to_rgb(hue, 1.0, 1.0)

            # 调用回调函数设置颜色
            self.set_color_callback(current_color)

            # 控制更新频率
            time.sleep(0.05)  # 20Hz 更新率


class DualityEffect(SoftwareEffect):
    def __init__(
        self,
        color1: Color,
        color2: Color,
        set_color_callback: Callable[[Color], None],
        speed: float = 0.2,
        transition: str = "sine",
    ):
        """
        初始化双色过渡效果

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

    def _interpolate_color(self, color1: Color, color2: Color, t: float) -> Color:
        """在两个颜色之间插值"""

        def lerp(a: int, b: int, t: float) -> int:
            return int(a + (b - a) * t)

        return Color(
            lerp(color1.R, color2.R, t),
            lerp(color1.G, color2.G, t),
            lerp(color1.B, color2.B, t),
        )

    def _get_transition_value(self, t: float) -> float:
        """根据过渡模式计算过渡值"""
        t = t % 1.0  # 确保 t 在 [0, 1] 范围内

        match self.transition:
            case "sine":
                # 使用正弦函数实现平滑过渡
                return (math.sin(t * math.pi * 2 - math.pi / 2) + 1) / 2
            case "linear":
                # 线性过渡
                return t
            case "ease":
                # 缓动过渡（使用三次方曲线）
                return 3 * t * t - 2 * t * t * t
            case _:
                return t

    def _run(self):
        """运行双色过渡效果"""
        start_time = time.time()
        while self._running:
            # 计算当前时间点的过渡进度
            current_time = time.time() - start_time
            progress = (current_time * self.speed) % 1.0

            # 应用过渡函数
            t = self._get_transition_value(progress)

            # 计算当前颜色
            current_color = self._interpolate_color(self.color1, self.color2, t)

            # 设置颜色
            self.set_color_callback(current_color)

            # 控制更新频率
            time.sleep(0.05)  # 20Hz 更新率
