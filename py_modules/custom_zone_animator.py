#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Zone Keyframe Animator
自定义区域关键帧动画器

Software-based keyframe animation engine for devices that support per-zone color control
but lack hardware keyframe mechanism (e.g., AyaNeo, OXP).
为支持分区颜色控制但缺少硬件关键帧机制的设备提供软件层关键帧动画引擎（如 AyaNeo、OXP）。

Similar to MSI's hardware keyframe system, but implemented entirely in software.
类似于 MSI 的硬件关键帧系统，但完全在软件层实现。
"""

import threading
import time
from typing import Callable, List, Optional

from config import logger, SOFTWARE_EFFECT_UPDATE_RATE


class KeyframeAnimator:
    """
    Keyframe-based animation engine for multi-zone LED control
    基于关键帧的多区域 LED 控制动画引擎
    
    Features:
    - Smooth interpolation between keyframes 关键帧之间平滑插值
    - Adjustable speed and brightness 可调节速度和亮度
    - Automatic frame timing 自动帧时序
    - Thread-safe operation 线程安全操作
    """
    
    def __init__(
        self,
        keyframes: List[List[List[int]]],
        set_zones_callback: Callable[[List[List[int]], List[List[int]]], None],
        speed: int = 10,
        brightness: int = 100,
        update_rate: float = SOFTWARE_EFFECT_UPDATE_RATE,
        num_left_zones: int = 4,
        num_right_zones: int = 4,
    ):
        """
        Initialize keyframe animator
        初始化关键帧动画器
        
        Args:
            keyframes: List of keyframes, each keyframe is a list of RGB colors for all zones
                       关键帧列表，每个关键帧是所有区域的 RGB 颜色列表
                       Format: [
                           [[R1,G1,B1], [R2,G2,B2], ..., [R8,G8,B8]],  # Frame 1
                           [[R1,G1,B1], [R2,G2,B2], ..., [R8,G8,B8]],  # Frame 2
                           ...
                       ]
            set_zones_callback: Callback function to set zone colors
                                设置区域颜色的回调函数
                                Function signature: (left_colors: List[List[int]], right_colors: List[List[int]]) -> None
            speed: Animation speed (0-20), higher is faster
                   动画速度（0-20），数值越大越快
                   Similar to MSI speed parameter
                   类似于 MSI 速度参数
            brightness: Overall brightness (0-100)
                        整体亮度（0-100）
            update_rate: Frame update rate in Hz (default 30 FPS)
                         帧更新频率（Hz），默认 30 FPS
            num_left_zones: Number of zones in left grip (default 4)
                            左手柄区域数量（默认 4）
            num_right_zones: Number of zones in right grip (default 4)
                             右手柄区域数量（默认 4）
        """
        if not keyframes or len(keyframes) < 1:
            raise ValueError("At least one keyframe is required")
        
        # Validate keyframe structure
        total_zones = num_left_zones + num_right_zones
        for i, frame in enumerate(keyframes):
            if len(frame) != total_zones:
                raise ValueError(
                    f"Keyframe {i} has {len(frame)} zones, expected {total_zones}"
                )
            for j, color in enumerate(frame):
                if len(color) != 3:
                    raise ValueError(
                        f"Keyframe {i}, zone {j}: Invalid RGB color {color}"
                    )
        
        self.keyframes = keyframes
        self.set_zones_callback = set_zones_callback
        self.speed = max(0, min(20, speed))
        self.brightness = max(0, min(100, brightness))
        self.update_rate = update_rate
        self.num_left_zones = num_left_zones
        self.num_right_zones = num_right_zones
        
        # Calculate per-frame duration based on speed
        # Hardware timing reference (from MSI): 
        # - Speed 20 (max): 200ms per frame
        # - Speed 0 (min): 5000ms per frame
        # 根据速度计算每帧持续时间
        # 硬件时序参考（来自 MSI）：
        # - 速度 20（最快）：每帧 200ms
        # - 速度 0（最慢）：每帧 5000ms
        min_frame_duration = 0.2    # 200ms at speed 20
        max_frame_duration = 5.0    # 5000ms at speed 0
        self.frame_duration = max_frame_duration - (
            (max_frame_duration - min_frame_duration) * self.speed / 20
        )
        
        # Threading control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info(
            f"KeyframeAnimator initialized: {len(keyframes)} frames, "
            f"speed={speed}, brightness={brightness}, "
            f"frame_duration={self.frame_duration:.2f}s"
        )
    
    def _interpolate_color(
        self, color1: List[int], color2: List[int], t: float
    ) -> List[int]:
        """
        Linearly interpolate between two RGB colors
        在两个 RGB 颜色之间线性插值
        
        Args:
            color1: Starting color [R, G, B]
            color2: Ending color [R, G, B]
            t: Interpolation factor (0.0 to 1.0)
               插值因子（0.0 到 1.0）
        
        Returns:
            Interpolated color [R, G, B]
        """
        return [
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t),
        ]
    
    def _interpolate_frame(
        self, frame1: List[List[int]], frame2: List[List[int]], t: float
    ) -> List[List[int]]:
        """
        Interpolate between two keyframes
        在两个关键帧之间插值
        
        Args:
            frame1: Starting keyframe
            frame2: Ending keyframe
            t: Interpolation factor (0.0 to 1.0)
        
        Returns:
            Interpolated frame with colors for all zones
        """
        return [
            self._interpolate_color(frame1[i], frame2[i], t)
            for i in range(len(frame1))
        ]
    
    def _apply_brightness(self, frame: List[List[int]]) -> List[List[int]]:
        """
        Apply brightness scaling to all colors in a frame
        对帧中所有颜色应用亮度缩放
        
        Args:
            frame: Frame with RGB colors for all zones
        
        Returns:
            Frame with brightness applied
        """
        if self.brightness >= 100:
            return frame
        
        brightness_factor = self.brightness / 100.0
        return [
            [
                int(color[0] * brightness_factor),
                int(color[1] * brightness_factor),
                int(color[2] * brightness_factor),
            ]
            for color in frame
        ]
    
    def _get_current_frame(self, progress: float) -> List[List[int]]:
        """
        Get interpolated frame at given animation progress
        获取给定动画进度的插值帧
        
        Args:
            progress: Animation progress (0.0 to 1.0 for one complete cycle)
                      动画进度（0.0 到 1.0 为一个完整周期）
        
        Returns:
            Interpolated and brightness-adjusted frame
        """
        num_frames = len(self.keyframes)
        
        # Calculate which two keyframes to interpolate between
        # 计算需要在哪两个关键帧之间插值
        total_progress = progress * num_frames
        frame_index = int(total_progress) % num_frames
        next_frame_index = (frame_index + 1) % num_frames
        frame_progress = total_progress - int(total_progress)
        
        # Interpolate between keyframes
        # 在关键帧之间插值
        frame1 = self.keyframes[frame_index]
        frame2 = self.keyframes[next_frame_index]
        interpolated = self._interpolate_frame(frame1, frame2, frame_progress)
        
        # Apply brightness
        # 应用亮度
        return self._apply_brightness(interpolated)
    
    def _split_frame(
        self, frame: List[List[int]]
    ) -> tuple[List[List[int]], List[List[int]]]:
        """
        Split complete frame into left and right zones
        将完整帧分割为左右区域
        
        Args:
            frame: Complete frame with all zone colors
        
        Returns:
            Tuple of (left_colors, right_colors)
        """
        left_colors = frame[: self.num_left_zones]
        right_colors = frame[self.num_left_zones : self.num_left_zones + self.num_right_zones]
        return left_colors, right_colors
    
    def _animation_loop(self):
        """
        Main animation loop
        主动画循环
        """
        start_time = time.time()
        cycle_duration = self.frame_duration * len(self.keyframes)
        sleep_interval = 1.0 / self.update_rate
        
        logger.info(
            f"Animation loop started: cycle_duration={cycle_duration:.2f}s, "
            f"update_rate={self.update_rate}Hz"
        )
        
        while self._running:
            try:
                # Calculate current animation progress
                # 计算当前动画进度
                elapsed = time.time() - start_time
                progress = (elapsed % cycle_duration) / cycle_duration
                
                # Get interpolated frame
                # 获取插值帧
                current_frame = self._get_current_frame(progress)
                
                # Split into left and right zones and send to device
                # 分割为左右区域并发送到设备
                left_colors, right_colors = self._split_frame(current_frame)
                self.set_zones_callback(left_colors, right_colors)
                
                # Sleep until next update
                # 休眠到下次更新
                time.sleep(sleep_interval)
                
            except Exception as e:
                logger.error(f"Error in animation loop: {e}", exc_info=True)
                time.sleep(0.1)  # Avoid tight loop on error
    
    def start(self):
        """
        Start animation
        启动动画
        
        For single frame: Set colors once without starting loop (static preview)
        对于单帧：只设置一次颜色，不启动循环（静态预览）
        For multiple frames: Start continuous animation loop
        对于多帧：启动连续动画循环
        """
        with self._lock:
            if self._running:
                logger.warning("Animation already running")
                return
            
            # Special handling for single frame (static preview)
            # 单帧特殊处理（静态预览）
            if len(self.keyframes) == 1:
                logger.info("Single frame detected, setting static colors without animation loop")
                # Get the single frame with brightness applied
                # 获取应用亮度后的单帧
                frame = self._apply_brightness(self.keyframes[0])
                # Split and send to device
                # 分割并发送到设备
                left_colors, right_colors = self._split_frame(frame)
                self.set_zones_callback(left_colors, right_colors)
                logger.debug(f"Set single frame static colors: brightness={self.brightness}")
                return
            
            # For multiple frames, start animation loop
            # 多帧情况，启动动画循环
            self._running = True
            self._thread = threading.Thread(target=self._animation_loop, daemon=True)
            self._thread.start()
            logger.info("Animation started")
    
    def stop(self):
        """
        Stop animation
        停止动画
        """
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._thread:
                self._thread.join(timeout=2.0)
                self._thread = None
            logger.info("Animation stopped")
    
    def is_running(self) -> bool:
        """Check if animation is currently running"""
        return self._running
    
    def update_config(
        self,
        keyframes: Optional[List[List[List[int]]]] = None,
        speed: Optional[int] = None,
        brightness: Optional[int] = None,
    ):
        """
        Update animation configuration
        更新动画配置
        
        Args:
            keyframes: New keyframes (optional)
            speed: New speed (optional)
            brightness: New brightness (optional)
        
        Note: Animation will continue seamlessly with new parameters
              动画将使用新参数无缝继续
        """
        with self._lock:
            if keyframes is not None:
                if not keyframes or len(keyframes) < 1:
                    logger.error("At least one keyframe is required")
                    return
                self.keyframes = keyframes
                logger.info(f"Keyframes updated: {len(keyframes)} frames")
            
            if speed is not None:
                self.speed = max(0, min(20, speed))
                # Recalculate frame duration
                min_frame_duration = 0.2
                max_frame_duration = 5.0
                self.frame_duration = max_frame_duration - (
                    (max_frame_duration - min_frame_duration) * self.speed / 20
                )
                logger.info(f"Speed updated: {self.speed} (frame_duration={self.frame_duration:.2f}s)")
            
            if brightness is not None:
                self.brightness = max(0, min(100, brightness))
                logger.info(f"Brightness updated: {self.brightness}")

