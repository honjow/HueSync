#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AyaNeo LED Device EC Control Module

Python implementation ported from the original C driver:
https://github.com/ShadowBlip/ayaneo-platform/blob/main/ayaneo-platform.c

Original C driver copyright:
Copyright (C) 2023-2024 Derek J. Clark <derekjohn.clark@gmail.com>
Copyright (C) 2023-2024 JELOS <https://github.com/JustEnoughLinuxOS>
Copyright (C) 2024, 2025 Sebastian Kranz <https://github.com/Lightwars>
Copyright (C) 2024 Trevor Heslop <https://github.com/SytheZN>

Python port maintains the same functionality and logic as the original C implementation.
Derived from ayaled originally developed by Maya Matuszczyk
<https://github.com/Maccraft123/ayaled>

This module provides LED control functionality for AYANEO x86 handheld devices
by communicating directly with the Embedded Controller (EC).
"""

import os
import time
import threading
from enum import Enum
from typing import List, Optional
from pathlib import Path

from config import logger, USE_AYANEO_ASYNC_WRITER
from ec import EC
from utils import Color

# Persistent storage path for suspend mode (for devices without kernel driver)
# 休眠模式持久化存储路径（用于没有内核驱动的设备）
CONFIG_DIR = "/var/lib/huesync"
SUSPEND_MODE_CONFIG_PATH = os.path.join(CONFIG_DIR, "ayaneo_suspend_mode")


class AyaNeoECConstants:
    """
    AyaNeo EC control related constant definitions

    Corresponding to C code macros, source:
    https://github.com/ShadowBlip/ayaneo-platform/blob/main/ayaneo-platform.c
    """

    # EC port addresses (corresponding to C: AYANEO_ADDR_PORT, AYANEO_DATA_PORT, AYANEO_HIGH_BYTE)
    ADDR_PORT = 0x4E
    DATA_PORT = 0x4F
    HIGH_BYTE = 0xD1

    # LED MC addresses - Modern devices (corresponding to C: AYANEO_LED_MC_ADDR_*)
    LED_MC_ADDR_L = 0xB0
    LED_MC_ADDR_R = 0x70
    LED_MC_ADDR_CLOSE_1 = 0x86
    LED_MC_ADDR_CLOSE_2 = 0xC6
    LED_MC_MODE_ADDR = 0x87
    LED_MC_MODE_HOLD = 0xA5
    LED_MC_MODE_RELEASE = 0x00

    # Legacy device registers (corresponding to C: AYANEO_LED_PWM_CONTROL etc.)
    LED_PWM_CONTROL = 0x6D
    LED_POS = 0xB1
    LED_BRIGHTNESS = 0xB2
    LED_MODE_REG = 0xBF

    # LED mode values (corresponding to C: AYANEO_LED_MODE_*)
    LED_MODE_RELEASE = 0x00
    LED_MODE_WRITE = 0x10
    LED_MODE_HOLD = 0xFE

    # LED group definitions (corresponding to C: AYANEO_LED_GROUP_*)
    LED_GROUP_LEFT = 0x01
    LED_GROUP_RIGHT = 0x02
    LED_GROUP_LEFT_RIGHT = 0x03
    LED_GROUP_BUTTON = 0x04

    # LED commands (corresponding to C: AYANEO_LED_CMD_*)
    LED_CMD_ENABLE_ADDR = 0x02
    LED_CMD_ENABLE_ON = 0xB1
    LED_CMD_ENABLE_OFF = 0x31
    LED_CMD_ENABLE_RESET = 0xC0
    LED_CMD_PATTERN_ADDR = 0x0F
    LED_CMD_PATTERN_OFF = 0x00
    LED_CMD_FADE_ADDR = 0x10
    LED_CMD_FADE_OFF = 0x00
    LED_CMD_ANIM_1_ADDR = 0x11
    LED_CMD_ANIM_2_ADDR = 0x12
    LED_CMD_ANIM_3_ADDR = 0x13
    LED_CMD_ANIM_4_ADDR = 0x14
    LED_CMD_ANIM_STATIC = 0x05
    LED_CMD_WATCHDOG_ADDR = 0x15
    LED_CMD_WATCHDOG_ON = 0x07

    # Delay constants (corresponding to C: AYANEO_LED_WRITE_DELAY_*)
    LED_WRITE_DELAY_MS = 0.001
    LED_WRITE_DELAY_LEGACY_MS = 0.002


class AyaNeoModel(Enum):
    """AyaNeo device model enumeration - corresponding to C: enum ayaneo_model"""

    AIR = 1
    AIR_1S = 2
    AIR_1S_LIMITED = 3
    AIR_PLUS = 4
    AIR_PLUS_MENDO = 5
    AIR_PRO = 6
    AYANEO_2 = 7
    AYANEO_2S = 8
    GEEK = 9
    GEEK_1S = 10
    KUN = 11
    SLIDE = 12


class AyaNeoSuspendMode(Enum):
    """Suspend mode enumeration - corresponding to C: enum AYANEO_LED_SUSPEND_MODE"""

    OEM = "oem"  # AYANEO_LED_SUSPEND_MODE_OEM
    KEEP = "keep"  # AYANEO_LED_SUSPEND_MODE_KEEP
    OFF = "off"  # AYANEO_LED_SUSPEND_MODE_OFF


class AyaNeoLEDDeviceEC:
    """
    AyaNeo LED device EC control class

    Python ported version, fully corresponding to C driver functionality:
    https://github.com/ShadowBlip/ayaneo-platform/blob/main/ayaneo-platform.c

    Provides LED control functionality for AYANEO x86 handheld devices
    by communicating directly with the Embedded Controller (EC).
    """

    def __init__(self):
        self.ec = EC()
        self.model = self._detect_model()
        
        # Load saved suspend mode from file (for devices without kernel driver)
        # 从文件加载保存的休眠模式（用于没有内核驱动的设备）
        self.suspend_mode = self._load_suspend_mode()

        # Software cache (corresponding to C: ayaneo_led_mc_update_color[3] and led_cdev->brightness)
        self.current_color = [0, 0, 0]  # RGB
        self.current_brightness = 255  # Total brightness, default maximum value (corresponding to C: max_brightness = 255)

        # Control status tracking - avoid frequent reinitialization during software effects
        self._has_control = False
        
        # Batch write mode - for async-like EC writes (mimics kernel driver's writer thread)
        self._batch_mode = False
        self._batch_commands = []
        
        # Async writer thread (mimics kernel driver's ayaneo_led_mc_writer)
        self._use_async_writer = USE_AYANEO_ASYNC_WRITER
        
        if self._use_async_writer:
            self._writer_lock = threading.Lock()
            self._update_required = 0
            self._update_color = [0, 0, 0]
            self._update_zones = None  # None = single color, or list of colors for zones
            self._writer_stop = threading.Event()
            self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
            self._writer_thread.start()
            logger.debug("AyaNeo async writer thread enabled")

        logger.info(f"AyaNeo LED Device initialized, model: {self.model}, suspend_mode: {self.suspend_mode.value}")
    
    def __del__(self):
        """Cleanup - stop writer thread gracefully"""
        try:
            if hasattr(self, '_writer_stop'):
                self._writer_stop.set()
            if hasattr(self, '_writer_thread') and self._writer_thread.is_alive():
                self._writer_thread.join(timeout=1.0)
        except:
            pass  # Ignore errors during cleanup

    def _load_suspend_mode(self) -> AyaNeoSuspendMode:
        """
        Load suspend mode from persistent storage.
        从持久化存储加载休眠模式。
        
        This provides persistence for devices without kernel driver support.
        为没有内核驱动支持的设备提供持久化。
        
        Returns:
            AyaNeoSuspendMode: Loaded mode, or default (OEM)
        """
        try:
            if os.path.exists(SUSPEND_MODE_CONFIG_PATH):
                with open(SUSPEND_MODE_CONFIG_PATH, "r") as f:
                    mode_str = f.read().strip()
                    if mode_str:
                        mode = AyaNeoSuspendMode(mode_str)
                        logger.info(f"Loaded suspend mode from file: {mode.value}")
                        return mode
        except Exception as e:
            logger.warning(f"Failed to load suspend mode from file: {e}")
        
        logger.info("Using default suspend mode: oem")
        return AyaNeoSuspendMode.OEM
    
    def _save_suspend_mode(self, mode: AyaNeoSuspendMode) -> None:
        """
        Save suspend mode to persistent storage.
        将休眠模式保存到持久化存储。
        """
        try:
            # Ensure directory exists
            # 确保目录存在
            Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
            
            with open(SUSPEND_MODE_CONFIG_PATH, "w") as f:
                f.write(mode.value)
            logger.debug(f"Saved suspend mode to file: {mode.value}")
        except Exception as e:
            logger.error(f"Failed to save suspend mode to file: {e}", exc_info=True)

    def _detect_model(self) -> Optional[AyaNeoModel]:
        """Detect AyaNeo device model - corresponding to C code dmi_table matching"""
        try:
            # Read DMI information
            with open("/sys/class/dmi/id/board_vendor", "r") as f:
                vendor = f.read().strip()
            with open("/sys/class/dmi/id/board_name", "r") as f:
                board_name = f.read().strip()

            if vendor != "AYANEO":
                logger.warning(f"Not an AYANEO device: {vendor}")
                return None

            # Corresponding to C code dmi_table mapping
            dmi_mapping = {
                "AIR": AyaNeoModel.AIR,
                "AIR 1S": AyaNeoModel.AIR_1S,
                "AIR 1S Limited": AyaNeoModel.AIR_1S_LIMITED,
                "AB05-AMD": AyaNeoModel.AIR_PLUS,
                "AB05-Mendocino": AyaNeoModel.AIR_PLUS_MENDO,
                "AIR Pro": AyaNeoModel.AIR_PRO,
                "AYANEO 2": AyaNeoModel.AYANEO_2,
                "AYANEO 2S": AyaNeoModel.AYANEO_2S,
                "GEEK": AyaNeoModel.GEEK,
                "GEEK 1S": AyaNeoModel.GEEK_1S,
                "AYANEO KUN": AyaNeoModel.KUN,
                "AS01": AyaNeoModel.SLIDE,
            }

            detected_model = dmi_mapping.get(board_name)
            if detected_model:
                logger.info(f"Detected AyaNeo model: {board_name} -> {detected_model}")
            else:
                logger.warning(f"Unknown AyaNeo model: {board_name}")

            return detected_model

        except Exception as e:
            logger.error(f"Failed to detect model: {e}")
            return None

    def _is_modern_device(self) -> bool:
        """Determine if it's a Modern device - corresponding to C code using ayaneo_led_mc_* devices"""
        return self.model in [AyaNeoModel.AIR_PLUS, AyaNeoModel.SLIDE]

    def _is_legacy_device(self) -> bool:
        """Determine if it's a Legacy device - corresponding to C code using ayaneo_led_mc_legacy_* devices"""
        return not self._is_modern_device()

    def _ec_write_ram(self, index: int, value: int) -> bool:
        """Corresponding to C code ec_write_ram function"""
        try:
            # C code: outb(AYANEO_HIGH_BYTE, AYANEO_DATA_PORT) + outb(index, AYANEO_DATA_PORT) | C代码: outb(AYANEO_HIGH_BYTE, AYANEO_DATA_PORT) + outb(index, AYANEO_DATA_PORT)
            full_address = (AyaNeoECConstants.HIGH_BYTE << 8) + index

            self.ec.RamWrite(
                AyaNeoECConstants.ADDR_PORT,  # 0x4e
                AyaNeoECConstants.DATA_PORT,  # 0x4f
                full_address,
                value,
            )

            return True
        except Exception as e:
            logger.error(f"EC write failed at 0x{index:02x}: {e}")
            return False

    def _ec_read_ram(self, index: int) -> Optional[int]:
        """Corresponding to C code ec_read_ram function"""
        try:
            full_address = (AyaNeoECConstants.HIGH_BYTE << 8) + index

            result = self.ec.RamRead(
                AyaNeoECConstants.ADDR_PORT, AyaNeoECConstants.DATA_PORT, full_address
            )

            return result
        except Exception as e:
            logger.error(f"EC read failed at 0x{index:02x}: {e}")
            return None

    # =================== Modern device LED control methods ===================

    def _led_mc_set(self, group: int, pos: int, brightness: int):
        """Corresponding to C: ayaneo_led_mc_set"""
        if group < 2:
            led_offset = AyaNeoECConstants.LED_MC_ADDR_L
            close_cmd = AyaNeoECConstants.LED_MC_ADDR_CLOSE_2
        else:
            led_offset = AyaNeoECConstants.LED_MC_ADDR_R
            close_cmd = AyaNeoECConstants.LED_MC_ADDR_CLOSE_1

        self._ec_write_ram(led_offset + pos, brightness)
        self._ec_write_ram(close_cmd, 0x01)
        time.sleep(AyaNeoECConstants.LED_WRITE_DELAY_MS)

    def _led_mc_hold(self):
        """Corresponding to C: ayaneo_led_mc_hold"""
        self._ec_write_ram(
            AyaNeoECConstants.LED_MC_MODE_ADDR, AyaNeoECConstants.LED_MC_MODE_HOLD
        )
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_release(self):
        """Corresponding to C: ayaneo_led_mc_release"""
        self._ec_write_ram(
            AyaNeoECConstants.LED_MC_MODE_ADDR, AyaNeoECConstants.LED_MC_MODE_RELEASE
        )

    def _led_mc_intensity(self, group: int, color: List[int], zones: List[int]):
        """Corresponding to C: ayaneo_led_mc_intensity"""
        for zone in zones:
            self._led_mc_set(group, zone, color[0])  # R
            self._led_mc_set(group, zone + 1, color[1])  # G
            self._led_mc_set(group, zone + 2, color[2])  # B
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_on(self):
        """Corresponding to C: ayaneo_led_mc_on"""
        # Enable LED
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_ON,
        )
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_ON,
        )

        # Turn off patterns and fading
        for group in [
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_GROUP_RIGHT,
        ]:
            self._led_mc_set(
                group,
                AyaNeoECConstants.LED_CMD_PATTERN_ADDR,
                AyaNeoECConstants.LED_CMD_PATTERN_OFF,
            )
            self._led_mc_set(
                group,
                AyaNeoECConstants.LED_CMD_FADE_ADDR,
                AyaNeoECConstants.LED_CMD_FADE_OFF,
            )

            # Set static animation
            for addr in [
                AyaNeoECConstants.LED_CMD_ANIM_1_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_2_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_3_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_4_ADDR,
            ]:
                self._led_mc_set(group, addr, AyaNeoECConstants.LED_CMD_ANIM_STATIC)

            # Enable watchdog
            self._led_mc_set(
                group,
                AyaNeoECConstants.LED_CMD_WATCHDOG_ADDR,
                AyaNeoECConstants.LED_CMD_WATCHDOG_ON,
            )

        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_off(self):
        """Corresponding to C: ayaneo_led_mc_off"""
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_OFF,
        )
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_OFF,
        )
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_reset(self):
        """Corresponding to C: ayaneo_led_mc_reset"""
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_RESET,
        )
        self._led_mc_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_RESET,
        )
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    # =================== Batch write mode (mimics kernel driver async behavior) ===================
    
    def _writer_loop(self):
        """
        Async writer thread - mimics kernel driver's ayaneo_led_mc_writer
        Continuously checks for update requests and applies them in background
        """
        try:
            while not self._writer_stop.is_set():
                count = 0
                color = None
                zones = None
                
                try:
                    with self._writer_lock:
                        count = self._update_required
                        if count:
                            # Copy data while holding lock
                            color = self._update_color.copy() if self._update_color else None
                            zones = self._update_zones.copy() if self._update_zones else None
                except Exception as e:
                    logger.error(f"Writer thread lock error: {e}")
                    time.sleep(0.1)
                    continue
                
                if count:
                    try:
                        # Apply the update (mimics ayaneo_led_mc_brightness_apply)
                        if zones is None and color is not None:
                            # Single color for all zones
                            self._apply_brightness_direct(color)
                        elif zones is not None:
                            # Custom zone colors
                            self._apply_custom_zones_direct(zones)
                        
                        with self._writer_lock:
                            self._update_required -= count
                    except Exception as e:
                        logger.error(f"Writer thread error: {e}")
                        with self._writer_lock:
                            self._update_required = 0
                else:
                    # Sleep when no updates (mimics usleep_range in kernel)
                    time.sleep(0.01)
        except Exception as e:
            logger.error(f"Writer thread fatal error: {e}")
    
    def _begin_batch_write(self):
        """Start batch write mode - queue EC commands instead of executing immediately"""
        self._batch_mode = True
        self._batch_commands = []
    
    def _end_batch_write(self):
        """End batch write mode - flush all queued commands rapidly"""
        if not self._batch_mode:
            return
        
        self._batch_mode = False
        
        # Execute all queued commands with WriteFast (mimics kernel driver speed)
        # WriteFast uses busy wait instead of sleep for EC status checks
        for cmd_type, args in self._batch_commands:
            if cmd_type == 'write':
                reg, val = args
                self.ec.WriteFast(reg, val)  # Fast write without sleep delays
            elif cmd_type == 'sleep':
                # Critical hardware delay - EC requires this between WRITE and HOLD
                time.sleep(args)
        
        self._batch_commands.clear()

    # =================== Legacy device LED control methods ===================

    def _led_mc_legacy_set(self, group: int, pos: int, brightness: int):
        """Corresponding to C: ayaneo_led_mc_legacy_set"""
        # Note: C code has ACPI lock, Python temporarily omits it | 注意：C代码有ACPI锁，Python暂时省略
        if self._batch_mode:
            # Batch mode - queue commands for later execution with WriteFast
            self._batch_commands.append(('write', (AyaNeoECConstants.LED_PWM_CONTROL, group)))
            self._batch_commands.append(('write', (AyaNeoECConstants.LED_POS, pos)))
            self._batch_commands.append(('write', (AyaNeoECConstants.LED_BRIGHTNESS, brightness)))
            self._batch_commands.append(('write', (AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_WRITE)))
            # CRITICAL: Sleep between WRITE and HOLD is EC hardware requirement
            self._batch_commands.append(('sleep', AyaNeoECConstants.LED_WRITE_DELAY_LEGACY_MS))
            self._batch_commands.append(('write', (AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_HOLD)))
        else:
            # Normal mode - immediate execution
            self.ec.Write(AyaNeoECConstants.LED_PWM_CONTROL, group)
            self.ec.Write(AyaNeoECConstants.LED_POS, pos)
            self.ec.Write(AyaNeoECConstants.LED_BRIGHTNESS, brightness)
            self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_WRITE)
            time.sleep(AyaNeoECConstants.LED_WRITE_DELAY_LEGACY_MS)
            self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_HOLD)
        time.sleep(0.001)

    def _led_mc_legacy_hold(self):
        """Corresponding to C: ayaneo_led_mc_legacy_hold"""
        self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_HOLD)

    def _led_mc_legacy_release(self):
        """Corresponding to C: ayaneo_led_mc_legacy_release"""
        self.ec.Write(
            AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_RELEASE
        )

    def _led_mc_legacy_intensity_single(self, group: int, color: List[int], zone: int):
        """Corresponding to C: ayaneo_led_mc_legacy_intensity_single"""
        self._led_mc_legacy_set(group, zone, color[0])
        self._led_mc_legacy_set(group, zone + 1, color[1])
        self._led_mc_legacy_set(group, zone + 2, color[2])

    def _led_mc_legacy_intensity(self, group: int, color: List[int] | List[List[int]], zones: List[int]):
        """
        Corresponding to C: ayaneo_led_mc_legacy_intensity
        
        Args:
            group: LED group (LEFT/RIGHT)
            color: Either a single RGB color [R,G,B] for all zones, or a list of colors [[R,G,B], ...] for each zone
            zones: Zone list [3,6,9,12]
        """
        # Enable batch mode - use WriteFast for all writes (except critical sleeps)
        self._begin_batch_write()
        
        # Check if it's a single color or multiple colors
        if len(color) > 0 and isinstance(color[0], list):
            # Multiple colors - one per zone
            for i, zone in enumerate(zones):
                self._led_mc_legacy_intensity_single(group, color[i], zone)
        else:
            # Single color - apply to all zones
            for zone in zones:
                self._led_mc_legacy_intensity_single(group, color, zone)
        
        # Flush batch - execute all queued commands with WriteFast
        self._end_batch_write()
        
        # Final commit - outside batch mode
        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_legacy_intensity_kun(self, group: int, color: List[int]):
        """Corresponding to C: ayaneo_led_mc_legacy_intensity_kun - KUN device special processing"""
        if group == AyaNeoECConstants.LED_GROUP_BUTTON:
            zone = 12
            remap_color = [color[2], color[0], color[1]]  # BGR mapping
            self._led_mc_legacy_intensity_single(
                AyaNeoECConstants.LED_GROUP_BUTTON, remap_color, zone
            )
            self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)
            return

        # Four regions' special color mapping (corresponding to complex mapping in C code) | 四个区域的特殊颜色映射 (对应C代码中的复杂映射)
        zone_mappings = [
            (3, [color[1], color[0], color[2]]),  # GRB
            (6, [color[1], color[2], color[0]]),  # GBR
            (9, [color[2], color[0], color[1]]),  # BRG
            (12, [color[2], color[1], color[0]]),  # BGR
        ]

        for zone, remap_color in zone_mappings:
            self._led_mc_legacy_intensity_single(group, remap_color, zone)

        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_legacy_on(self):
        """Corresponding to C: ayaneo_led_mc_legacy_on"""
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_ON,
        )
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_ON,
        )
        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_legacy_off(self):
        """Corresponding to C: ayaneo_led_mc_legacy_off"""
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_OFF,
        )
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_OFF,
        )
        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_legacy_reset(self):
        """Corresponding to C: ayaneo_led_mc_legacy_reset"""
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_LEFT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_RESET,
        )
        self._led_mc_legacy_set(
            AyaNeoECConstants.LED_GROUP_RIGHT,
            AyaNeoECConstants.LED_CMD_ENABLE_ADDR,
            AyaNeoECConstants.LED_CMD_ENABLE_RESET,
        )
        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    # =================== Color processing methods ===================

    def _scale_color(self, color: List[int], max_value: int) -> List[int]:
        """Corresponding to C: ayaneo_led_mc_scale_color"""
        scaled = []
        for c in color:
            c_scaled = int(c * max_value / 255)
            # Prevent left-right brightness difference | 防止左右亮度差异
            if c_scaled == 0 and c > 0:
                c_scaled = 1
            scaled.append(min(c_scaled, 255))
        return scaled

    def _apply_brightness_direct(self, color_list: List[int]):
        """Direct execution version - called by writer thread"""
        # Ensure we have control before writing
        self._take_control()
        
        color = Color(color_list[0], color_list[1], color_list[2])
        color_l = [color.R, color.G, color.B]
        color_r = [color.R, color.G, color.B]
        color_b = [color.R, color.G, color.B]
        zones = [3, 6, 9, 12]  # Standard 4 zones

        # Apply different scaling strategies based on device model (corresponding to switch statement in C code) | 根据设备型号应用不同的缩放策略 (对应C代码中的switch语句)
        match self.model:
            case AyaNeoModel.AIR | AyaNeoModel.AIR_PRO | AyaNeoModel.AIR_1S:
                # AIR series standard processing
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones
                )
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.AIR_1S_LIMITED:
                # AIR 1S Limited special right scaling
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 204)  # Special scaling value
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones
                )
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case (
                AyaNeoModel.GEEK
                | AyaNeoModel.GEEK_1S
                | AyaNeoModel.AYANEO_2
                | AyaNeoModel.AYANEO_2S
            ):
                # GEEK and AYANEO 2 series
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones
                )
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.AIR_PLUS_MENDO:
                # AIR Plus Mendocino - Legacy device, lower scaling value
                color_l = self._scale_color(color_l, 64)
                color_r = self._scale_color(color_r, 32)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones
                )
                self._led_mc_legacy_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.AIR_PLUS:
                # AIR Plus - Modern device, lower scaling value
                color_l = self._scale_color(color_l, 64)
                color_r = self._scale_color(color_r, 32)
                self._led_mc_on()
                self._led_mc_intensity(AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones)
                self._led_mc_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.SLIDE:
                # SLIDE - Modern device, standard scaling
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                self._led_mc_on()
                self._led_mc_intensity(AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones)
                self._led_mc_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.KUN:
                # KUN - Special three-region processing (including button)
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                color_b = self._scale_color(color_b, 192)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity_kun(
                    AyaNeoECConstants.LED_GROUP_LEFT, color_l
                )
                self._led_mc_legacy_intensity_kun(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r
                )
                self._led_mc_legacy_intensity_kun(
                    AyaNeoECConstants.LED_GROUP_BUTTON, color_b
                )

            case _:
                # Default processing: Unknown device or None
                if self.model is None:
                    logger.warning("No device model detected, skipping LED control")
                    return

                # Other models use Legacy device default processing
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                if self._is_legacy_device():
                    self._led_mc_legacy_on()
                    self._led_mc_legacy_intensity(
                        AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones
                    )
                    self._led_mc_legacy_intensity(
                        AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                    )
                else:
                    logger.warning(f"Unknown modern device model: {self.model}")
    
    def _apply_brightness(self, color: Color):
        """
        Apply brightness - async if writer thread enabled, sync otherwise
        """
        if self._use_async_writer:
            # Async version - queues update for writer thread
            with self._writer_lock:
                self._update_color = [color.R, color.G, color.B]
                self._update_zones = None  # None indicates single color mode
                self._update_required += 1
        else:
            # Sync version - direct execution
            self._apply_brightness_direct([color.R, color.G, color.B])

    # =================== Control management ===================

    def _take_control(self):
        """Corresponding to C: ayaneo_led_mc_take_control"""
        if self._has_control:
            return  # Already have control, avoid repeated initialization

        if self._is_legacy_device():
            self._led_mc_legacy_hold()
            self._led_mc_legacy_reset()
            self._led_mc_legacy_off()
        else:
            self._led_mc_hold()
            self._led_mc_reset()
            self._led_mc_off()

        self._has_control = True

    def _release_control(self):
        """Corresponding to C: ayaneo_led_mc_release_control"""
        if not self._has_control:
            return  # Don't have control, no need to release

        if self._is_legacy_device():
            self._led_mc_legacy_reset()
            self._led_mc_legacy_release()
        else:
            self._led_mc_reset()
            self._led_mc_release()

        self._has_control = False

    # =================== Public interface ===================

    def set_led_color(self, color: Color):
        """Set LED color - main public interface (async version)"""
        # Update software cache (corresponding to C: ayaneo_led_mc_update_color[])
        self.current_color = [color.R, color.G, color.B]

        # Calculate brightness-adjusted color (corresponding to C code brightness * intensity / max_brightness logic) | 计算亮度调整后的颜色 (对应C代码中brightness * intensity / max_brightness的逻辑)
        if self.current_brightness < 255:
            adjusted_color = Color(
                min(255, int(color.R * self.current_brightness / 255)),
                min(255, int(color.G * self.current_brightness / 255)),
                min(255, int(color.B * self.current_brightness / 255)),
            )
        else:
            adjusted_color = color

        # Queue update for writer thread (control management handled by writer)
        self._apply_brightness(adjusted_color)

        logger.debug(
            f"LED color set to R:{color.R}, G:{color.G}, B:{color.B}, brightness:{self.current_brightness}"
        )

    def get_led_color(self) -> Color:
        """Get current LED color (from software cache) - C code has no hardware read, only cache"""
        return Color(
            self.current_color[0], self.current_color[1], self.current_color[2]
        )

    def _apply_custom_zones_direct(self, zone_data):
        """
        Direct execution version - called by writer thread
        zone_data: dict with 'left_colors', 'right_colors', 'button_color'
        """
        left_colors = zone_data['left_colors']
        right_colors = zone_data['right_colors']
        button_color = zone_data.get('button_color')
        
        # Already validated before queuing, but safety check
        if len(left_colors) != 4 or len(right_colors) != 4:
            logger.error("left_colors and right_colors must each contain exactly 4 RGB values")
            return
        
        zones = [3, 6, 9, 12]  # Standard 4 zones
        
        # Take control of LEDs
        self._take_control()
        
        # Apply brightness adjustment to each color
        def adjust_brightness(rgb: List[int]) -> List[int]:
            if self.current_brightness < 255:
                return [
                    min(255, int(rgb[0] * self.current_brightness / 255)),
                    min(255, int(rgb[1] * self.current_brightness / 255)),
                    min(255, int(rgb[2] * self.current_brightness / 255)),
                ]
            return rgb
        
        # Apply brightness to all colors
        left_adjusted = [adjust_brightness(c) for c in left_colors]
        right_adjusted = [adjust_brightness(c) for c in right_colors]
        
        # Handle different device types
        if self._is_modern_device():
            # Modern devices (AIR_PLUS, SLIDE)
            self._led_mc_on()
            
            # Apply model-specific scaling
            scaling = 64 if self.model == AyaNeoModel.AIR_PLUS else 192  # SLIDE uses 192
            
            for i, zone in enumerate(zones):
                left_scaled = self._scale_color(left_adjusted[i], scaling)
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT, zone, left_scaled[0])
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT, zone + 1, left_scaled[1])
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT, zone + 2, left_scaled[2])
            
            # Right side with different scaling for AIR_PLUS
            right_scaling = 32 if self.model == AyaNeoModel.AIR_PLUS else 192
            for i, zone in enumerate(zones):
                right_scaled = self._scale_color(right_adjusted[i], right_scaling)
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_RIGHT, zone, right_scaled[0])
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_RIGHT, zone + 1, right_scaled[1])
                self._led_mc_set(AyaNeoECConstants.LED_GROUP_RIGHT, zone + 2, right_scaled[2])
            
            self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)
            
        else:
            # Legacy devices
            self._led_mc_legacy_on()
            
            # Determine scaling based on model
            if self.model == AyaNeoModel.AIR_PLUS_MENDO:
                left_scaling, right_scaling = 64, 32
            elif self.model == AyaNeoModel.AIR_1S_LIMITED:
                left_scaling, right_scaling = 192, 204
            else:
                left_scaling, right_scaling = 192, 192
            
            if self.model == AyaNeoModel.KUN:
                # KUN requires special color channel mapping for each zone
                zone_channel_mappings = [
                    [1, 0, 2],  # Zone 3: GRB
                    [1, 2, 0],  # Zone 6: GBR  
                    [2, 0, 1],  # Zone 9: BRG
                    [2, 1, 0],  # Zone 12: BGR
                ]
                
                # Prepare all colors with scaling and remapping
                left_colors_remapped = []
                right_colors_remapped = []
                for i in range(len(zones)):
                    left_scaled = self._scale_color(left_adjusted[i], left_scaling)
                    mapping = zone_channel_mappings[i]
                    left_colors_remapped.append([left_scaled[mapping[0]], left_scaled[mapping[1]], left_scaled[mapping[2]]])
                    
                    right_scaled = self._scale_color(right_adjusted[i], right_scaling)
                    right_colors_remapped.append([right_scaled[mapping[0]], right_scaled[mapping[1]], right_scaled[mapping[2]]])
                
                # Use exactly the same pattern as single-color (in _apply_brightness)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(AyaNeoECConstants.LED_GROUP_LEFT, left_colors_remapped, zones)
                self._led_mc_legacy_intensity(AyaNeoECConstants.LED_GROUP_RIGHT, right_colors_remapped, zones)
                
                # Handle button zone if provided
                if button_color:
                    button_adjusted = adjust_brightness(button_color)
                    button_scaled = self._scale_color(button_adjusted, 192)
                    button_remapped = [button_scaled[2], button_scaled[0], button_scaled[1]]  # BGR for button
                    self._led_mc_legacy_intensity_single(AyaNeoECConstants.LED_GROUP_BUTTON, button_remapped, 12)
            else:
                # Standard legacy devices
                # Prepare all colors with scaling
                left_colors_scaled = [self._scale_color(left_adjusted[i], left_scaling) for i in range(len(zones))]
                right_colors_scaled = [self._scale_color(right_adjusted[i], right_scaling) for i in range(len(zones))]
                
                # Use exactly the same pattern as single-color (in _apply_brightness)
                self._led_mc_legacy_on()
                self._led_mc_legacy_intensity(AyaNeoECConstants.LED_GROUP_LEFT, left_colors_scaled, zones)
                self._led_mc_legacy_intensity(AyaNeoECConstants.LED_GROUP_RIGHT, right_colors_scaled, zones)
        
        # Update software cache with average color (for compatibility with get_led_color)
        avg_r = sum(c[0] for c in left_colors + right_colors) // 8
        avg_g = sum(c[1] for c in left_colors + right_colors) // 8
        avg_b = sum(c[2] for c in left_colors + right_colors) // 8
        self.current_color = [avg_r, avg_g, avg_b]
        
        logger.debug(f"Custom zone colors set - Left: {left_colors}, Right: {right_colors}")
    
    def set_custom_zone_colors(self, left_colors: List[List[int]], right_colors: List[List[int]], button_color: Optional[List[int]] = None):
        """
        Set custom colors for individual LED zones - async if writer enabled, sync otherwise
        
        Args:
            left_colors: List of 4 RGB colors for left grip zones
            right_colors: List of 4 RGB colors for right grip zones
            button_color: Optional RGB color for button zone (KUN only)
        """
        # Validate inputs
        if len(left_colors) != 4 or len(right_colors) != 4:
            logger.error("left_colors and right_colors must each contain exactly 4 RGB values")
            return
        
        for colors in [left_colors, right_colors]:
            for color in colors:
                if len(color) != 3 or any(c < 0 or c > 255 for c in color):
                    logger.error(f"Invalid RGB color: {color}. Each value must be 0-255")
                    return
        
        if self._use_async_writer:
            # Async version - queue update for writer thread
            with self._writer_lock:
                self._update_zones = {
                    'left_colors': left_colors,
                    'right_colors': right_colors,
                    'button_color': button_color
                }
                self._update_color = None  # Not used for zone mode
                self._update_required += 1
        else:
            # Sync version - direct execution
            self._apply_custom_zones_direct({
                'left_colors': left_colors,
                'right_colors': right_colors,
                'button_color': button_color
            })

    def set_brightness(self, brightness: int):
        """
        Set total brightness - corresponding to C: ayaneo_led_mc_brightness_set

        Args:
            brightness: Brightness value (0-255)
        """
        if brightness < 0 or brightness > 255:
            logger.error(f"Invalid brightness value: {brightness}. Must be 0-255")
            return

        self.current_brightness = brightness
        logger.debug(f"LED brightness set to: {brightness}")

        # If there's a current color, reapply with new brightness
        if self.current_color != [0, 0, 0]:
            # Calculate brightness-adjusted color (corresponding to calculation logic in C code) | 计算亮度调整后的颜色 (对应C代码中的计算逻辑)
            adjusted_color = Color(
                min(255, int(self.current_color[0] * brightness / 255)),
                min(255, int(self.current_color[1] * brightness / 255)),
                min(255, int(self.current_color[2] * brightness / 255)),
            )

            # Apply adjusted color
            self._take_control()
            self._apply_brightness(adjusted_color)

    def get_brightness(self) -> int:
        """Get current total brightness - corresponding to C: ayaneo_led_mc_brightness_get"""
        return self.current_brightness

    def get_led_brightness(self) -> int:
        """Get current LED brightness - corresponding to C: ayaneo_led_mc_brightness_get (backward compatibility)"""
        return self.get_brightness()

    def get_suspend_mode(self) -> str:
        """Get suspend mode - corresponding to C: suspend_mode_show"""
        return self.suspend_mode.value

    def list_suspend_modes(self) -> str:
        """
        List all available suspend modes - corresponding to C: suspend_mode_show

        Returns:
            str: Formatted mode list string
        """
        modes = []
        for mode in AyaNeoSuspendMode:
            if mode == self.suspend_mode:
                modes.append(f"[{mode.value}]")
            else:
                modes.append(mode.value)

        return " ".join(modes)

    def get_available_suspend_modes(self) -> List[str]:
        """
        Get list of all available suspend modes

        Returns:
            List[str]: List of all available modes
        """
        return [mode.value for mode in AyaNeoSuspendMode]

    def set_suspend_mode(self, mode: str):
        """
        Set suspend mode with file-based persistence.
        设置休眠模式并持久化到文件。
        
        Note: For devices with kernel driver, huesync.py will use sysfs instead.
        注意：对于有内核驱动的设备，huesync.py 会使用 sysfs。
        
        Corresponding to C: suspend_mode_store
        """
        try:
            if mode == "":
                mode = "oem"
            
            self.suspend_mode = AyaNeoSuspendMode(mode)
            
            # Persist to file (survives plugin restart)
            # 持久化到文件（插件重启后保留）
            self._save_suspend_mode(self.suspend_mode)
            
            logger.info(f"Suspend mode set to: {mode} (persisted to file)")
        except ValueError:
            valid_modes = [m.value for m in AyaNeoSuspendMode]
            logger.error(f"Invalid suspend mode: {mode}. Valid modes: {valid_modes}")
            raise ValueError(f"Invalid suspend mode. Valid modes: {valid_modes}")
        except Exception as e:
            logger.error(f"Failed to set suspend mode: {e}", exc_info=True)
            raise

    def suspend(self):
        """Suspend processing - corresponding to C: ayaneo_platform_suspend"""
        match self.suspend_mode:
            case AyaNeoSuspendMode.OEM:
                self._release_control()
            case AyaNeoSuspendMode.OFF:
                self._take_control()
                if self._is_legacy_device():
                    self._led_mc_legacy_off()
                else:
                    self._led_mc_off()
            case AyaNeoSuspendMode.KEEP:
                # KEEP mode does nothing, keep current state
                pass

        logger.info(f"LED suspended with mode: {self.suspend_mode.value}")

    def resume(self):
        """Resume processing - corresponding to C: ayaneo_platform_resume"""
        # Resume and regain control
        self._has_control = False  # Reset status, ensure reinitialization
        self._take_control()

        # Reapply last color
        if self.current_color != [0, 0, 0]:
            color = Color(
                self.current_color[0], self.current_color[1], self.current_color[2]
            )
            self._apply_brightness(color)

        logger.info("LED resumed")
