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

import time
from enum import Enum
from typing import List, Optional

from config import logger
from ec import EC
from utils import Color


class AyaNeoECConstants:
    """
    AyaNeo EC控制相关常量定义

    对应C代码中的宏定义，来源：
    https://github.com/ShadowBlip/ayaneo-platform/blob/main/ayaneo-platform.c
    """

    # EC端口地址 (对应C: AYANEO_ADDR_PORT, AYANEO_DATA_PORT, AYANEO_HIGH_BYTE)
    ADDR_PORT = 0x4E
    DATA_PORT = 0x4F
    HIGH_BYTE = 0xD1

    # LED MC地址 - Modern设备 (对应C: AYANEO_LED_MC_ADDR_*)
    LED_MC_ADDR_L = 0xB0
    LED_MC_ADDR_R = 0x70
    LED_MC_ADDR_CLOSE_1 = 0x86
    LED_MC_ADDR_CLOSE_2 = 0xC6
    LED_MC_MODE_ADDR = 0x87
    LED_MC_MODE_HOLD = 0xA5
    LED_MC_MODE_RELEASE = 0x00

    # Legacy设备寄存器 (对应C: AYANEO_LED_PWM_CONTROL等)
    LED_PWM_CONTROL = 0x6D
    LED_POS = 0xB1
    LED_BRIGHTNESS = 0xB2
    LED_MODE_REG = 0xBF

    # LED模式值 (对应C: AYANEO_LED_MODE_*)
    LED_MODE_RELEASE = 0x00
    LED_MODE_WRITE = 0x10
    LED_MODE_HOLD = 0xFE

    # LED组定义 (对应C: AYANEO_LED_GROUP_*)
    LED_GROUP_LEFT = 0x01
    LED_GROUP_RIGHT = 0x02
    LED_GROUP_LEFT_RIGHT = 0x03
    LED_GROUP_BUTTON = 0x04

    # LED命令 (对应C: AYANEO_LED_CMD_*)
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

    # 延迟常量 (对应C: AYANEO_LED_WRITE_DELAY_*)
    LED_WRITE_DELAY_MS = 0.001
    LED_WRITE_DELAY_LEGACY_MS = 0.002


class AyaNeoModel(Enum):
    """AyaNeo设备型号枚举 - 对应C: enum ayaneo_model"""

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
    """Suspend模式枚举 - 对应C: enum AYANEO_LED_SUSPEND_MODE"""

    OEM = "oem"  # AYANEO_LED_SUSPEND_MODE_OEM
    KEEP = "keep"  # AYANEO_LED_SUSPEND_MODE_KEEP
    OFF = "off"  # AYANEO_LED_SUSPEND_MODE_OFF


class AyaNeoLEDDeviceEC:
    """
    AyaNeo LED设备EC控制类

    Python移植版本，完全对应C驱动程序的功能：
    https://github.com/ShadowBlip/ayaneo-platform/blob/main/ayaneo-platform.c

    提供AyaNeo x86掌机设备的LED控制功能，通过直接与嵌入式控制器(EC)通信实现。
    """

    def __init__(self):
        self.ec = EC()
        self.model = self._detect_model()
        self.suspend_mode = AyaNeoSuspendMode.OEM

        # 软件缓存 (对应C: ayaneo_led_mc_update_color[3] 和 led_cdev->brightness)
        self.current_color = [0, 0, 0]  # RGB
        self.current_brightness = (
            255  # 总亮度，默认最大值 (对应C: max_brightness = 255)
        )

        logger.info(f"AyaNeo LED Device initialized, model: {self.model}")

    def _detect_model(self) -> Optional[AyaNeoModel]:
        """检测AyaNeo设备型号 - 对应C代码的dmi_table匹配"""
        try:
            # 读取DMI信息
            with open("/sys/class/dmi/id/board_vendor", "r") as f:
                vendor = f.read().strip()
            with open("/sys/class/dmi/id/board_name", "r") as f:
                board_name = f.read().strip()

            if vendor != "AYANEO":
                logger.warning(f"Not an AYANEO device: {vendor}")
                return None

            # 对应C代码的dmi_table映射
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
        """判断是否为Modern设备 - 对应C代码中使用ayaneo_led_mc_*的设备"""
        return self.model in [AyaNeoModel.AIR_PLUS, AyaNeoModel.SLIDE]

    def _is_legacy_device(self) -> bool:
        """判断是否为Legacy设备 - 对应C代码中使用ayaneo_led_mc_legacy_*的设备"""
        return not self._is_modern_device()

    def _ec_write_ram(self, index: int, value: int) -> bool:
        """对应C代码的ec_write_ram函数"""
        try:
            # C代码: outb(AYANEO_HIGH_BYTE, AYANEO_DATA_PORT) + outb(index, AYANEO_DATA_PORT)
            full_address = (AyaNeoECConstants.HIGH_BYTE << 8) + index
            self.ec.RamWrite(
                AyaNeoECConstants.ADDR_PORT,  # 0x4e
                AyaNeoECConstants.DATA_PORT,  # 0x4f
                full_address,
                value,
            )
            return True
        except Exception as e:
            logger.error(f"EC RAM write failed at 0x{index:02x}: {e}")
            return False

    def _ec_read_ram(self, index: int) -> Optional[int]:
        """对应C代码的ec_read_ram函数"""
        try:
            full_address = (AyaNeoECConstants.HIGH_BYTE << 8) + index
            return self.ec.RamRead(
                AyaNeoECConstants.ADDR_PORT, AyaNeoECConstants.DATA_PORT, full_address
            )
        except Exception as e:
            logger.error(f"EC RAM read failed at 0x{index:02x}: {e}")
            return None

    # =================== Modern设备LED控制方法 ===================

    def _led_mc_set(self, group: int, pos: int, brightness: int):
        """对应C: ayaneo_led_mc_set"""
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
        """对应C: ayaneo_led_mc_hold"""
        self._ec_write_ram(
            AyaNeoECConstants.LED_MC_MODE_ADDR, AyaNeoECConstants.LED_MC_MODE_HOLD
        )
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_release(self):
        """对应C: ayaneo_led_mc_release"""
        self._ec_write_ram(
            AyaNeoECConstants.LED_MC_MODE_ADDR, AyaNeoECConstants.LED_MC_MODE_RELEASE
        )

    def _led_mc_intensity(self, group: int, color: List[int], zones: List[int]):
        """对应C: ayaneo_led_mc_intensity"""
        for zone in zones:
            self._led_mc_set(group, zone, color[0])  # R
            self._led_mc_set(group, zone + 1, color[1])  # G
            self._led_mc_set(group, zone + 2, color[2])  # B
        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_on(self):
        """对应C: ayaneo_led_mc_on"""
        # 启用LED
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

        # 关闭图案和淡化
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

            # 设置静态动画
            for addr in [
                AyaNeoECConstants.LED_CMD_ANIM_1_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_2_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_3_ADDR,
                AyaNeoECConstants.LED_CMD_ANIM_4_ADDR,
            ]:
                self._led_mc_set(group, addr, AyaNeoECConstants.LED_CMD_ANIM_STATIC)

            # 启用看门狗
            self._led_mc_set(
                group,
                AyaNeoECConstants.LED_CMD_WATCHDOG_ADDR,
                AyaNeoECConstants.LED_CMD_WATCHDOG_ON,
            )

        self._led_mc_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_off(self):
        """对应C: ayaneo_led_mc_off"""
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
        """对应C: ayaneo_led_mc_reset"""
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

    # =================== Legacy设备LED控制方法 ===================

    def _led_mc_legacy_set(self, group: int, pos: int, brightness: int):
        """对应C: ayaneo_led_mc_legacy_set"""
        # 注意：C代码有ACPI锁，Python暂时省略
        self.ec.Write(AyaNeoECConstants.LED_PWM_CONTROL, group)
        self.ec.Write(AyaNeoECConstants.LED_POS, pos)
        self.ec.Write(AyaNeoECConstants.LED_BRIGHTNESS, brightness)
        self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_WRITE)

        time.sleep(AyaNeoECConstants.LED_WRITE_DELAY_LEGACY_MS)

        self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_HOLD)

    def _led_mc_legacy_hold(self):
        """对应C: ayaneo_led_mc_legacy_hold"""
        self.ec.Write(AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_HOLD)

    def _led_mc_legacy_release(self):
        """对应C: ayaneo_led_mc_legacy_release"""
        self.ec.Write(
            AyaNeoECConstants.LED_MODE_REG, AyaNeoECConstants.LED_MODE_RELEASE
        )

    def _led_mc_legacy_intensity_single(self, group: int, color: List[int], zone: int):
        """对应C: ayaneo_led_mc_legacy_intensity_single"""
        self._led_mc_legacy_set(group, zone, color[0])
        self._led_mc_legacy_set(group, zone + 1, color[1])
        self._led_mc_legacy_set(group, zone + 2, color[2])

    def _led_mc_legacy_intensity(self, group: int, color: List[int], zones: List[int]):
        """对应C: ayaneo_led_mc_legacy_intensity"""
        for zone in zones:
            self._led_mc_legacy_intensity_single(group, color, zone)
        self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)

    def _led_mc_legacy_intensity_kun(self, group: int, color: List[int]):
        """对应C: ayaneo_led_mc_legacy_intensity_kun - KUN设备特殊处理"""
        if group == AyaNeoECConstants.LED_GROUP_BUTTON:
            zone = 12
            remap_color = [color[2], color[0], color[1]]  # BGR mapping
            self._led_mc_legacy_intensity_single(
                AyaNeoECConstants.LED_GROUP_BUTTON, remap_color, zone
            )
            self._led_mc_legacy_set(AyaNeoECConstants.LED_GROUP_LEFT_RIGHT, 0x00, 0x00)
            return

        # 四个区域的特殊颜色映射 (对应C代码中的复杂映射)
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
        """对应C: ayaneo_led_mc_legacy_on"""
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
        """对应C: ayaneo_led_mc_legacy_off"""
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
        """对应C: ayaneo_led_mc_legacy_reset"""
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

    # =================== 颜色处理方法 ===================

    def _scale_color(self, color: List[int], max_value: int) -> List[int]:
        """对应C: ayaneo_led_mc_scale_color"""
        scaled = []
        for c in color:
            c_scaled = int(c * max_value / 255)
            # 防止左右亮度差异
            if c_scaled == 0 and c > 0:
                c_scaled = 1
            scaled.append(min(c_scaled, 255))
        return scaled

    def _apply_brightness(self, color: Color):
        """对应C: ayaneo_led_mc_brightness_apply"""
        color_l = [color.R, color.G, color.B]
        color_r = [color.R, color.G, color.B]
        color_b = [color.R, color.G, color.B]
        zones = [3, 6, 9, 12]  # 标准4区域

        # 根据设备型号应用不同的缩放策略 (对应C代码中的switch语句)
        match self.model:
            case AyaNeoModel.AIR | AyaNeoModel.AIR_PRO | AyaNeoModel.AIR_1S:
                # AIR系列标准处理
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
                # AIR 1S Limited特殊右侧缩放
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 204)  # 特殊缩放值
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
                # GEEK和AYANEO 2系列
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
                # AIR Plus Mendocino - Legacy设备，较低缩放值
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
                # AIR Plus - Modern设备，较低缩放值
                color_l = self._scale_color(color_l, 64)
                color_r = self._scale_color(color_r, 32)
                self._led_mc_on()
                self._led_mc_intensity(AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones)
                self._led_mc_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.SLIDE:
                # SLIDE - Modern设备，标准缩放
                color_l = self._scale_color(color_l, 192)
                color_r = self._scale_color(color_r, 192)
                self._led_mc_on()
                self._led_mc_intensity(AyaNeoECConstants.LED_GROUP_LEFT, color_l, zones)
                self._led_mc_intensity(
                    AyaNeoECConstants.LED_GROUP_RIGHT, color_r, zones
                )

            case AyaNeoModel.KUN:
                # KUN - 特殊的三区域处理（包含按钮）
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
                # 默认处理：未知设备或None
                if self.model is None:
                    logger.warning("No device model detected, skipping LED control")
                    return

                # 其他型号使用Legacy设备默认处理
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

    # =================== 控制权管理 ===================

    def _take_control(self):
        """对应C: ayaneo_led_mc_take_control"""
        if self._is_legacy_device():
            self._led_mc_legacy_hold()
            self._led_mc_legacy_reset()
            self._led_mc_legacy_off()
        else:
            self._led_mc_hold()
            self._led_mc_reset()
            self._led_mc_off()

    def _release_control(self):
        """对应C: ayaneo_led_mc_release_control"""
        if self._is_legacy_device():
            self._led_mc_legacy_reset()
            self._led_mc_legacy_release()
        else:
            self._led_mc_reset()
            self._led_mc_release()

    # =================== 公共接口 ===================

    def set_led_color(self, color: Color):
        """设置LED颜色 - 主要公共接口"""
        # 更新软件缓存 (对应C: ayaneo_led_mc_update_color[])
        self.current_color = [color.R, color.G, color.B]

        # 计算亮度调整后的颜色 (对应C代码中brightness * intensity / max_brightness的逻辑)
        if self.current_brightness < 255:
            adjusted_color = Color(
                min(255, int(color.R * self.current_brightness / 255)),
                min(255, int(color.G * self.current_brightness / 255)),
                min(255, int(color.B * self.current_brightness / 255)),
            )
        else:
            adjusted_color = color

        # 获取控制权并应用颜色
        self._take_control()
        self._apply_brightness(adjusted_color)

        logger.debug(
            f"LED color set to R:{color.R}, G:{color.G}, B:{color.B}, brightness:{self.current_brightness}"
        )

    def get_led_color(self) -> Color:
        """获取当前LED颜色 (从软件缓存) - C代码没有硬件读取，只有缓存"""
        return Color(
            self.current_color[0], self.current_color[1], self.current_color[2]
        )

    def set_brightness(self, brightness: int):
        """
        设置总亮度 - 对应C: ayaneo_led_mc_brightness_set

        Args:
            brightness: 亮度值 (0-255)
        """
        if brightness < 0 or brightness > 255:
            logger.error(f"Invalid brightness value: {brightness}. Must be 0-255")
            return

        self.current_brightness = brightness
        logger.debug(f"LED brightness set to: {brightness}")

        # 如果有当前颜色，重新应用亮度
        if self.current_color != [0, 0, 0]:
            # 计算亮度调整后的颜色 (对应C代码中的计算逻辑)
            adjusted_color = Color(
                min(255, int(self.current_color[0] * brightness / 255)),
                min(255, int(self.current_color[1] * brightness / 255)),
                min(255, int(self.current_color[2] * brightness / 255)),
            )

            # 应用调整后的颜色
            self._take_control()
            self._apply_brightness(adjusted_color)

    def get_brightness(self) -> int:
        """获取当前总亮度 - 对应C: ayaneo_led_mc_brightness_get"""
        return self.current_brightness

    def get_led_brightness(self) -> int:
        """获取当前LED亮度 - 对应C: ayaneo_led_mc_brightness_get (向后兼容)"""
        return self.get_brightness()

    def get_suspend_mode(self) -> str:
        """获取suspend模式 - 对应C: suspend_mode_show"""
        return self.suspend_mode.value

    def list_suspend_modes(self) -> str:
        """
        列出所有可用的suspend模式 - 对应C: suspend_mode_show

        返回格式与C代码相同：当前模式用方括号标记，其他模式直接列出
        例如: "[oem] keep off" 表示当前模式是oem，可用模式有keep和off

        Returns:
            str: 格式化的模式列表字符串
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
        获取所有可用的suspend模式列表

        Returns:
            List[str]: 所有可用模式的列表
        """
        return [mode.value for mode in AyaNeoSuspendMode]

    def set_suspend_mode(self, mode: str):
        """设置suspend模式 - 对应C: suspend_mode_store"""
        try:
            self.suspend_mode = AyaNeoSuspendMode(mode)
            logger.info(f"Suspend mode set to: {mode}")
        except ValueError:
            valid_modes = [m.value for m in AyaNeoSuspendMode]
            logger.error(f"Invalid suspend mode: {mode}. Valid modes: {valid_modes}")
            raise ValueError(f"Invalid suspend mode. Valid modes: {valid_modes}")

    def suspend(self):
        """挂起处理 - 对应C: ayaneo_platform_suspend"""
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
                # KEEP模式不做任何操作，保持当前状态
                pass

        logger.info(f"LED suspended with mode: {self.suspend_mode.value}")

    def resume(self):
        """恢复处理 - 对应C: ayaneo_platform_resume"""
        self._take_control()

        # 重新应用最后的颜色
        if self.current_color != [0, 0, 0]:
            color = Color(
                self.current_color[0], self.current_color[1], self.current_color[2]
            )
            self._apply_brightness(color)

        logger.info("LED resumed")
