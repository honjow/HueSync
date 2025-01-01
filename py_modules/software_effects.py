import math
import threading
import time
from typing import Optional, Callable

from utils import Color


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
        speed: float = 1.0,
    ):
        """
        初始化呼吸灯效果

        Args:
            base_color (Color): 基础颜色
            set_color_callback: 设置颜色的回调函数
            speed (float): 呼吸速度，默认为1.0
        """
        super().__init__()
        self.base_color = base_color
        self.set_color_callback = set_color_callback
        self.speed = speed
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
        start_time = time.time()
        while self._running:
            # 使用正弦函数生成平滑的亮度变化
            # 将时间映射到0-1的亮度值
            current_time = time.time() - start_time
            brightness = (math.sin(current_time * self.speed) + 1) / 2

            # 应用亮度到颜色
            current_color = self._apply_brightness(self.base_color, brightness)

            # 调用回调函数设置颜色
            self.set_color_callback(current_color)

            # 控制更新频率
            time.sleep(0.05)  # 20Hz 更新率


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
