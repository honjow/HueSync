# OneXPlayer/AOKZOE Implementation Improvements
# OneXPlayer/AOKZOE 实现改进建议

## 当前状态 Current Status

HueSync的OneXPlayer实现基于HandheldCompanion的逆向工程，但缺少HHD中的许多高级特性。
HueSync's OneXPlayer implementation is based on HandheldCompanion reverse engineering, but lacks many advanced features from HHD.

## 关键缺失功能 Critical Missing Features

### 1. 初始化命令 Initialization Commands

**问题 Issue:**
- HueSync不发送初始化命令
- 可能导致设备在某些状态下无响应

**HHD实现 HHD Implementation:**
```python
# hid_v1.py
INITIALIZE = [
    gen_cmd(0xB4, "0238020101010101000000020102000000030103000000040104000000050105000000060106000000070107000000080108000000090109000000"),
    gen_cmd(0xB4, "02380202010a010a0000000b010b0000000c010c0000000d010d0000000e010e0000000f010f000000100110000000220200000000230200000000"),
    gen_intercept(False),
]
```

**建议 Recommendation:**
在`OneXLEDDeviceHID.is_ready()`中添加初始化：
```python
def is_ready(self) -> bool:
    if self.hid_device:
        return True
    
    # ... 现有的设备查找代码 ...
    
    if found_device:
        self.hid_device = hid.Device(path=device["path"])
        self._initialize_device()  # ← 新增
        return True
    return False

def _initialize_device(self):
    """Send initialization commands to device"""
    protocol = self._check_protocol()
    if protocol == Protocol.X1_MINI:
        # HID v1 initialization
        init_cmds = [
            self._gen_cmd_v1(0xB4, "0238020101010101..."),
            self._gen_cmd_v1(0xB4, "02380202010a010a..."),
            self._gen_intercept_v1(False),
        ]
    else:
        # HID v2 has no initialization
        init_cmds = []
    
    for cmd in init_cmds:
        self.hid_device.write(cmd)
        time.sleep(0.05)
```

---

### 2. 命令队列系统 Command Queue System

**问题 Issue:**
- 直接发送命令可能导致冲突
- 没有延迟控制

**HHD实现 HHD Implementation:**
```python
self.queue_cmd = deque(maxlen=10)
self.next_send = 0
WRITE_DELAY = 0.05

def consume(self, events):
    curr = time.perf_counter()
    if self.queue_cmd and curr - self.next_send > 0:
        cmd = self.queue_cmd.popleft()
        self.dev.write(cmd)
        self.next_send = curr + WRITE_DELAY
```

**建议 Recommendation:**
添加命令队列到`OneXLEDDeviceHID`：
```python
from collections import deque
import time

class OneXLEDDeviceHID:
    def __init__(self, ...):
        # ... 现有代码 ...
        self._cmd_queue = deque(maxlen=10)
        self._next_send = 0
        self._write_delay = 0.05
    
    def _queue_command(self, cmd: bytes):
        """Queue a command for sending"""
        self._cmd_queue.append(cmd)
    
    def _flush_queue(self):
        """Send queued commands with proper delays"""
        while self._cmd_queue:
            curr = time.perf_counter()
            if curr - self._next_send < 0:
                time.sleep(self._next_send - curr)
            
            cmd = self._cmd_queue.popleft()
            self.hid_device.write(cmd)
            self._next_send = time.perf_counter() + self._write_delay
    
    def set_led_color_new(self, main_color: Color, mode: RGBMode) -> bool:
        # ... 生成命令 ...
        self._queue_command(cmd)
        self._flush_queue()  # ← 替代直接write
        return True
```

---

### 3. OXP品牌预设模式 OXP Brand Preset Modes

**问题 Issue:**
- 只支持Solid和Rainbow
- HHD支持9种预设灯效

**HHD支持的模式 HHD Supported Modes:**
```python
RGB_MODES = {
    "monster_woke": 0x0D,
    "flowing": 0x03,
    "sunset": 0x0B,
    "neon": 0x05,
    "dreamy": 0x07,
    "cyberpunk": 0x09,
    "colorful": 0x0C,
    "aurora": 0x01,
    "sun": 0x08,
    "aok": 0x0E,  # AOKZOE特有
}
```

**建议 Recommendation:**

#### Step 1: 添加到 `utils.py`
```python
class RGBMode(Enum):
    # ... 现有模式 ...
    OXP_MONSTER_WOKE = "oxp_monster_woke"
    OXP_FLOWING = "oxp_flowing"
    OXP_SUNSET = "oxp_sunset"
    OXP_NEON = "oxp_neon"
    OXP_DREAMY = "oxp_dreamy"
    OXP_CYBERPUNK = "oxp_cyberpunk"
    OXP_COLORFUL = "oxp_colorful"
    OXP_AURORA = "oxp_aurora"
    OXP_SUN = "oxp_sun"
```

#### Step 2: 更新 `onexplayer.py`
```python
@property
def hardware_supported_modes(self) -> list[RGBMode]:
    return [
        RGBMode.Disabled,
        RGBMode.Solid,
        RGBMode.Rainbow,
        # OXP预设模式
        RGBMode.OXP_MONSTER_WOKE,
        RGBMode.OXP_FLOWING,
        RGBMode.OXP_SUNSET,
        RGBMode.OXP_NEON,
        RGBMode.OXP_DREAMY,
        RGBMode.OXP_CYBERPUNK,
        RGBMode.OXP_COLORFUL,
        RGBMode.OXP_AURORA,
        RGBMode.OXP_SUN,
    ]

def get_mode_capabilities(self) -> dict[RGBMode, RGBModeCapabilities]:
    capabilities = super().get_mode_capabilities()
    
    # 所有OXP预设模式支持亮度控制
    oxp_modes = [
        RGBMode.OXP_MONSTER_WOKE, RGBMode.OXP_FLOWING,
        RGBMode.OXP_SUNSET, RGBMode.OXP_NEON,
        RGBMode.OXP_DREAMY, RGBMode.OXP_CYBERPUNK,
        RGBMode.OXP_COLORFUL, RGBMode.OXP_AURORA,
        RGBMode.OXP_SUN,
    ]
    
    for mode in oxp_modes:
        capabilities[mode] = RGBModeCapabilities(
            mode=mode,
            color=False,
            color2=False,
            speed=False,
            brightness=True,
        )
    
    return capabilities
```

#### Step 3: 添加映射函数到 `onex_led_device_hid.py`
```python
def _map_oxp_mode(mode: RGBMode) -> str | None:
    """Map RGBMode to OXP mode string"""
    oxp_map = {
        RGBMode.OXP_MONSTER_WOKE: "monster_woke",
        RGBMode.OXP_FLOWING: "flowing",
        RGBMode.OXP_SUNSET: "sunset",
        RGBMode.OXP_NEON: "neon",
        RGBMode.OXP_DREAMY: "dreamy",
        RGBMode.OXP_CYBERPUNK: "cyberpunk",
        RGBMode.OXP_COLORFUL: "colorful",
        RGBMode.OXP_AURORA: "aurora",
        RGBMode.OXP_SUN: "sun",
    }
    return oxp_map.get(mode)

def set_led_color_new(self, main_color: Color, mode: RGBMode) -> bool:
    if not self.is_ready():
        return False

    if self._check_protocol() == Protocol.X1_MINI:
        from .hhd.oxp_hid_v1 import gen_rgb_mode, gen_rgb_solid
    else:
        from .hhd.oxp_hid_v2 import gen_rgb_mode, gen_rgb_solid

    # 检查是否是OXP预设模式
    oxp_mode_str = _map_oxp_mode(mode)
    if oxp_mode_str:
        cmd = gen_rgb_mode(oxp_mode_str)
    elif mode == RGBMode.Disabled:
        cmd = gen_rgb_solid(0, 0, 0)
    elif mode == RGBMode.Solid:
        cmd = gen_rgb_solid(main_color.R, main_color.G, main_color.B)
    elif mode == RGBMode.Rainbow:
        cmd = gen_rgb_mode("neon")
    else:
        return False

    # ... 发送命令 ...
```

#### Step 4: 前端UI更新

在 `src/i18n/*.json` 添加翻译：
```json
{
  "OXP_MONSTER_WOKE": "Monster Woke",
  "OXP_FLOWING": "Flowing",
  "OXP_SUNSET": "Sunset",
  "OXP_NEON": "Neon",
  "OXP_DREAMY": "Dreamy",
  "OXP_CYBERPUNK": "Cyberpunk",
  "OXP_COLORFUL": "Colorful",
  "OXP_AURORA": "Aurora",
  "OXP_SUN": "Sun"
}
```

---

### 4. 产品型号配置系统 Product Model Configuration

**问题 Issue:**
- 只有VID/PID检测
- 没有针对特定型号的优化

**HHD实现 HHD Implementation:**
```python
CONFS = {
    "ONEXPLAYER F1": {
        "protocol": "mixed",  # HID + Serial
        "rgb": True,
    },
    "ONEXPLAYER X1 mini": {
        "protocol": "hid_v1",
        "mapping": X1_MINI_MAPPING,
    },
    "ONEXPLAYER G1 i": {
        "protocol": "hid_v1_g1",
        "g1": True,
    },
    # ... 20+ 型号
}
```

**建议 Recommendation:**

创建 `py_modules/devices/onexplayer_configs.py`:
```python
from enum import Enum

class OXPProtocol(Enum):
    HID_V1 = "hid_v1"
    HID_V2 = "hid_v2"
    HID_V1_G1 = "hid_v1_g1"
    SERIAL = "serial"
    MIXED = "mixed"  # HID + Serial
    NONE = "none"

class OXPConfig:
    def __init__(
        self,
        name: str,
        protocol: OXPProtocol,
        rgb: bool = True,
        rgb_secondary: bool = False,
        g1: bool = False,
    ):
        self.name = name
        self.protocol = protocol
        self.rgb = rgb
        self.rgb_secondary = rgb_secondary
        self.g1 = g1

ONEXPLAYER_CONFIGS = {
    # OneXFly系列
    "ONEXPLAYER F1": OXPConfig(
        "ONEXPLAYER F1", OXPProtocol.MIXED
    ),
    "ONEXPLAYER F1 EVA-01": OXPConfig(
        "ONEXPLAYER F1 EVA-01", OXPProtocol.MIXED
    ),
    "ONEXPLAYER F1 OLED": OXPConfig(
        "ONEXPLAYER F1 OLED", OXPProtocol.MIXED
    ),
    
    # X1 Mini系列
    "ONEXPLAYER X1 mini": OXPConfig(
        "ONEXPLAYER X1 Mini", OXPProtocol.HID_V1
    ),
    
    # X1系列（Serial）
    "ONEXPLAYER X1 A": OXPConfig(
        "ONEXPLAYER X1 (AMD)", OXPProtocol.SERIAL,
        rgb_secondary=True
    ),
    "ONEXPLAYER X1 i": OXPConfig(
        "ONEXPLAYER X1 (Intel)", OXPProtocol.SERIAL,
        rgb_secondary=True
    ),
    
    # G1系列
    "ONEXPLAYER G1 i": OXPConfig(
        "ONEXPLAYER G1 (Intel)", OXPProtocol.HID_V1_G1,
        g1=True
    ),
    
    # OneXPlayer 2（无RGB）
    "ONEXPLAYER 2": OXPConfig(
        "ONEXPLAYER 2", OXPProtocol.NONE,
        rgb=False
    ),
    
    # AOKZOE
    "AOKZOE A1 AR07": OXPConfig(
        "AOKZOE A1", OXPProtocol.NONE,
        rgb=False
    ),
    "AOKZOE A1X": OXPConfig(
        "AOKZOE A1X", OXPProtocol.HID_V2
    ),
}

def get_config(product_name: str) -> OXPConfig | None:
    """Get configuration for product name"""
    # 精确匹配
    if product_name in ONEXPLAYER_CONFIGS:
        return ONEXPLAYER_CONFIGS[product_name]
    
    # 模糊匹配
    if "ONEXPLAYER" in product_name:
        return OXPConfig(
            product_name,
            OXPProtocol.HID_V2 if "X1" in product_name else OXPProtocol.MIXED,
            rgb=True,
            rgb_secondary="X1" in product_name and "mini" not in product_name.lower()
        )
    
    if "AOKZOE" in product_name:
        return OXPConfig(product_name, OXPProtocol.NONE, rgb=False)
    
    return None
```

更新 `onexplayer.py`:
```python
from .onexplayer_configs import get_config, OXPProtocol

class OneXLEDDevice(BaseLEDDevice):
    def __init__(self):
        super().__init__()
        self._config = get_config(PRODUCT_NAME)
        
        if self._config:
            logger.info(f"Detected {self._config.name}, protocol: {self._config.protocol}")
        else:
            logger.warning(f"Unknown OneXPlayer model: {PRODUCT_NAME}")
```

---

### 5. Mixed模式支持 Mixed Mode Support

**问题 Issue:**
- F1系列需要同时使用HID和Serial
- HueSync只能选其一

**HHD实现 HHD Implementation:**
```python
# F1使用Mixed模式
case "mixed":
    found_vendor = bool(
        enumerate_unique(vid=XFLY_VID, pid=XFLY_PID, ...)
    ) and bool(get_serial()[0])
```

**建议 Recommendation:**

更新 `_set_hardware_color`:
```python
def _set_hardware_color(
    self,
    mode: RGBMode | None = None,
    color: Color | None = None,
    color2: Color | None = None,
    init: bool = False,
    speed: str | None = None,
) -> None:
    if not color:
        return
    
    config = get_config(PRODUCT_NAME)
    
    if config and config.protocol == OXPProtocol.MIXED:
        # F1系列：HID控制摇杆，Serial控制中央区域
        self.set_onex_color_hid(color, mode, speed)
        if config.rgb_secondary and color2:
            self.set_onex_color_serial(color2, mode)
    elif config and config.protocol == OXPProtocol.SERIAL:
        self.set_onex_color_serial(color, mode)
    else:
        self.set_onex_color_hid(color, mode, speed)
```

---

### 6. G1设备支持 G1 Device Support

**问题 Issue:**
- G1有5个独立灯区
- HueSync只能控制整体

**HHD的G1区域 HHD G1 Zones:**
```python
# side值：
# 0x00 = 全部
# 0x01 = 左手柄
# 0x02 = 右手柄
# 0x03 = 中央V区
# 0x04 = 触摸键盘
# 0x05 = 前面板三角
```

**建议 Recommendation:**

这需要大量UI改动，建议：
- 低优先级
- 等其他功能完成后再考虑
- 或者只控制全部区域（side=0x00）

---

## 实施计划 Implementation Plan

### Phase 1: 稳定性修复（P0）
1. ✅ 添加初始化命令
2. ✅ 实现命令队列
3. ✅ 修复协议检测

**预计时间：** 2-3小时

### Phase 2: 功能增强（P1）
4. ✅ 添加OXP预设模式（9种）
5. ✅ 产品型号配置系统
6. ✅ Mixed模式支持

**预计时间：** 3-4小时

### Phase 3: 高级功能（P2）
7. ⚠️ G1多区域支持
8. ⚠️ 优化Serial实现

**预计时间：** 4-6小时

---

## 测试清单 Testing Checklist

### 必测设备 Must Test
- [ ] ONEXPLAYER F1/F1 OLED (Mixed模式)
- [ ] ONEXPLAYER X1 Mini (HID v1)
- [ ] AOKZOE A1X (HID v2)

### 应测设备 Should Test
- [ ] ONEXPLAYER X1 (Serial)
- [ ] ONEXPLAYER G1 (HID v1 G1)
- [ ] ONEXPLAYER 2 (无RGB)

---

## 参考资源 References

1. **HHD源码：**
   - `/home/gamer/git/hhd/src/hhd/device/oxp/`

2. **HandheldCompanion：**
   - https://github.com/Valkirie/HandheldCompanion

3. **OXP-Sensors驱动：**
   - https://github.com/KyTheBytes/oxp-platform-driver

---

## 风险评估 Risk Assessment

| 改动 | 风险等级 | 说明 |
|------|---------|------|
| 初始化命令 | 🟢 低 | 可能需要设备测试验证 |
| 命令队列 | 🟢 低 | 纯软件逻辑 |
| OXP模式 | 🟡 中 | 需要UI翻译和测试 |
| 产品配置 | 🟢 低 | 向后兼容 |
| Mixed模式 | 🟡 中 | 需要F1设备测试 |
| G1支持 | 🔴 高 | 大量UI改动 |

---

## 总结 Summary

HueSync的OneXPlayer实现**功能基础但不完整**：
- ✅ 基础RGB控制正常
- ⚠️ 缺少稳定性保障（初始化、队列）
- ❌ 缺少高级功能（预设模式、多协议）

**建议优先实施Phase 1和2**，以提升稳定性和用户体验。

