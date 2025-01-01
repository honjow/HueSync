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

    return Color(
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255)
    )


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
    def __init__(self, base_color: Color, set_color_callback: Callable[[Color], None], speed: float = 1.0):
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
            int(color.B * brightness)
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
    def __init__(self, set_color_callback: Callable[[Color], None], speed: float = 1.0):
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
