"""
OneXPlayer Product Configuration System
OneXPlayer产品配置系统

Maps product names to device-specific configurations including
protocol types, RGB capabilities, and device features.

将产品名称映射到设备特定配置，包括协议类型、RGB功能和设备特性。

Based on HHD: hhd/device/oxp/const.py
"""

from enum import Enum


class OXPProtocol(Enum):
    """
    OneXPlayer HID protocol versions.
    OneXPlayer HID协议版本。
    """
    HID_V1 = "hid_v1"          # X1 Mini series - older protocol
    HID_V2 = "hid_v2"          # XFly, A1X - newer protocol
    HID_V1_G1 = "hid_v1_g1"    # G1 series - v1 with 5 LED zones
    SERIAL = "serial"          # X1 series - serial port communication
    MIXED = "mixed"            # F1 series - both HID and Serial
    NONE = "none"              # No RGB support


class OXPConfig:
    """
    Configuration for a specific OneXPlayer model.
    特定OneXPlayer型号的配置。
    """
    
    def __init__(
        self,
        name: str,
        protocol: OXPProtocol,
        rgb: bool = True,
        rgb_secondary: bool = False,
        g1: bool = False,
    ):
        """
        Args:
            name: Display name of the device
            protocol: Communication protocol to use
            rgb: Whether device has RGB LEDs
            rgb_secondary: Whether device has secondary RGB zone (X1 series)
            g1: Whether device is G1 model (5 LED zones)
        """
        self.name = name
        self.protocol = protocol
        self.rgb = rgb
        self.rgb_secondary = rgb_secondary
        self.g1 = g1


# OneXFly F1 series configuration
# OneXFly F1系列配置
OXP_F1_CONF = OXPConfig(
    name="ONEXPLAYER ONEXFLY",
    protocol=OXPProtocol.MIXED,
    rgb=True,
)

# OneXPlayer 2 series configuration (no RGB)
# OneXPlayer 2系列配置（无RGB）
OXP_2_CONF = OXPConfig(
    name="ONEXPLAYER 2",
    protocol=OXPProtocol.NONE,
    rgb=False,
)

# AOKZOE A1 series configuration (no RGB)
# AOKZOE A1系列配置（无RGB）
AOKZOE_CONF = OXPConfig(
    name="AOKZOE A1",
    protocol=OXPProtocol.NONE,
    rgb=False,
)


# Product name to configuration mapping
# 产品名称到配置的映射
ONEXPLAYER_CONFIGS = {
    # ========== OneXFly F1 Series ==========
    "ONEXPLAYER F1": OXP_F1_CONF,
    "ONEXPLAYER F1 EVA-01": OXP_F1_CONF,
    "ONEXPLAYER F1L": OXP_F1_CONF,
    "ONEXPLAYER F1 OLED": OXP_F1_CONF,
    "ONEXPLAYER F1Pro": OXP_F1_CONF,
    "ONEXPLAYER F1 EVA-02": OXP_F1_CONF,
    
    # ========== X1 Mini Series (HID v1) ==========
    "ONEXPLAYER X1 mini": OXPConfig(
        name="ONEXPLAYER X1 Mini",
        protocol=OXPProtocol.HID_V1,
        rgb=True,
    ),
    "ONEXPLAYER X1Mini Pro": OXPConfig(
        name="ONEXPLAYER X1 Mini Pro",
        protocol=OXPProtocol.HID_V1,
        rgb=True,
    ),

    "ONEXPLAYER X1Air": OXPConfig(
        name="ONEXPLAYER X1 Air",
        protocol=OXPProtocol.HID_V1,
        rgb=True,
    ),
    
    # ========== X1 Series (Serial) ==========
    "ONEXPLAYER X1 A": OXPConfig(
        name="ONEXPLAYER X1 (AMD)",
        protocol=OXPProtocol.SERIAL,
        rgb=True,
        rgb_secondary=True,
    ),
    "ONEXPLAYER X1z": OXPConfig(
        name="ONEXPLAYER X1 (AMD)",
        protocol=OXPProtocol.SERIAL,
        rgb=True,
        rgb_secondary=True,
    ),
    "ONEXPLAYER X1Pro": OXPConfig(
        name="ONEXPLAYER X1 Pro (AMD)",
        protocol=OXPProtocol.SERIAL,
        rgb=True,
        rgb_secondary=True,
    ),
    "ONEXPLAYER X1Pro EVA-02": OXPConfig(
        name="ONEXPLAYER X1Pro EVA-02 (Intel)",
        protocol=OXPProtocol.SERIAL,
        rgb=True,
        rgb_secondary=True,
    ),
    "ONEXPLAYER X1 i": OXPConfig(
        name="ONEXPLAYER X1 (Intel)",
        protocol=OXPProtocol.SERIAL,
        rgb=True,
        rgb_secondary=True,
    ),
    
    # ========== G1 Series (HID v1 G1) ==========
    "ONEXPLAYER G1 i": OXPConfig(
        name="ONEXPLAYER G1 (Intel)",
        protocol=OXPProtocol.HID_V1_G1,
        rgb=True,
        g1=True,
    ),
    "ONEXPLAYER G1 A": OXPConfig(
        name="ONEXPLAYER G1 (AMD)",
        protocol=OXPProtocol.HID_V1_G1,
        rgb=True,
        g1=True,
    ),
    
    # ========== OneXPlayer 2 Series (No RGB) ==========
    "ONEXPLAYER 2": OXP_2_CONF,
    "ONEXPLAYER 2 ARP23": OXP_2_CONF,
    "ONEXPLAYER 2 GA18": OXP_2_CONF,
    "ONEXPLAYER 2 PRO ARP23": OXP_2_CONF,
    "ONEXPLAYER 2 PRO ARP23 EVA-01": OXP_2_CONF,
    
    # ========== Mini Pro (HID v2) ==========
    "ONEXPLAYER Mini Pro": OXPConfig(
        name="ONEXPLAYER Mini Pro",
        protocol=OXPProtocol.HID_V2,
        rgb=True,
    ),
    
    # ========== Original OneXPlayer ==========
    "ONE XPLAYER": OXPConfig(
        name="ONE XPLAYER",
        protocol=OXPProtocol.HID_V1,
        rgb=True,
    ),
    "ONEXPLAYER mini A07": OXPConfig(
        name="ONEXPLAYER mini",
        protocol=OXPProtocol.HID_V1,
        rgb=True,
    ),
    
    # ========== AOKZOE Series ==========
    "AOKZOE A1 AR07": AOKZOE_CONF,
    "AOKZOE A1 Pro": AOKZOE_CONF,
    "AOKZOE A2 Pro": AOKZOE_CONF,
    "AOKZOE A1X": OXPConfig(
        name="AOKZOE A1X",
        protocol=OXPProtocol.HID_V2,
        rgb=True,
    ),
}


def get_config(product_name: str) -> OXPConfig | None:
    """
    Get device configuration for a product name.
    获取产品名称的设备配置。
    
    Tries exact match first, then falls back to fuzzy matching
    for unknown models.
    
    首先尝试精确匹配，然后对未知型号进行模糊匹配。
    
    Args:
        product_name: DMI product name from /sys/devices/virtual/dmi/id/product_name
        
    Returns:
        OXPConfig if recognized, None if not an OneXPlayer/AOKZOE device
    """
    # Exact match
    # 精确匹配
    if product_name in ONEXPLAYER_CONFIGS:
        return ONEXPLAYER_CONFIGS[product_name]
    
    # Fuzzy matching for unknown OneXPlayer models
    # 对未知OneXPlayer型号进行模糊匹配
    if "ONEXPLAYER" in product_name:
        # X1 series (non-mini) typically use serial
        # X1系列（非mini）通常使用串口
        if "X1" in product_name and "mini" not in product_name.lower():
            return OXPConfig(
                name=product_name,
                protocol=OXPProtocol.SERIAL,
                rgb=True,
                rgb_secondary=True,
            )
        
        # Default to HID v2 for unknown models
        # 未知型号默认使用HID v2
        return OXPConfig(
            name=product_name,
            protocol=OXPProtocol.HID_V2,
            rgb=True,
        )
    
    # Fuzzy matching for unknown AOKZOE models
    # 对未知AOKZOE型号进行模糊匹配
    if "AOKZOE" in product_name:
        # Assume newer AOKZOE models might have RGB
        # 假设较新的AOKZOE型号可能有RGB
        if "A1X" in product_name or "A2X" in product_name:
            return OXPConfig(
                name=product_name,
                protocol=OXPProtocol.HID_V2,
                rgb=True,
            )
        
        # Default to no RGB for unknown AOKZOE
        # 未知AOKZOE默认无RGB
        return OXPConfig(
            name=product_name,
            protocol=OXPProtocol.NONE,
            rgb=False,
        )
    
    # Not an OneXPlayer or AOKZOE device
    # 不是OneXPlayer或AOKZOE设备
    return None

