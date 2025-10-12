# Legion Go 电源灯控制脚本

## 概述

`legion_power_light.py` 是一个用于控制 Legion Go / Legion Go S 电源指示灯的独立脚本。

**特点:**
- ✅ 无需 `acpi_call` 内核模块
- ✅ 适用于 SteamOS 等只读文件系统
- ✅ 自动检测设备型号 (Legion Go 或 Legion Go S)
- ✅ 直接通过 EC (Embedded Controller) 端口访问硬件
- ✅ 支持两种设备的不同寄存器配置

## 技术原理

### 硬件访问方式

脚本通过 `/dev/port` 直接访问 EC 端口 (0x62/0x66),无需任何内核模块:

1. **读取 EC 寄存器**: 通过 0x80 命令读取指定偏移的寄存器值
2. **写入 EC 寄存器**: 通过 0x81 命令写入新值到寄存器
3. **修改特定位**: 只修改控制电源灯的位,保留其他位不变

### 设备差异

| 设备 | 产品型号 | 寄存器偏移 | 位位置 | 字段名 |
|------|----------|-----------|--------|--------|
| Legion Go (原版) | 83E1, 83N0, 83N1 | 0x52 | bit 5 | LEDP |
| Legion Go S | 83L3, 83N6, 83Q2, 83Q3 | 0x10 | bit 6 | LPBL |

**共同点**: 两种设备都使用反向逻辑
- bit = 0 → 电源灯开启
- bit = 1 → 电源灯关闭

### DSDT 分析

配置来源于 [hhd-dev/hwinfo](https://github.com/hhd-dev/hwinfo) 仓库中的 ACPI DSDT 表:

**Legion Go 原版:**
```asl
# /devices/legion_go/acpi-N3CN29WW/decoded/dsdt.dsl
OperationRegion (ECMM, SystemMemory, 0xFE0B0300, 0xFF)
Field (ECMM, AnyAcc, Lock, Preserve)
{
    Offset (0x52),
    LEDP, 1,  # bit 5: 电源灯控制
    ...
}

Method (SLT2, 1, Serialized)
{
    If ((C00A == One))  { LEDP = Zero }  # 开灯
    If ((C00A == Zero)) { LEDP = One  }  # 关灯
}
```

**Legion Go S:**
```asl
# /devices/legion_go_s/acpi/QCCN17WW-query-rename/decoded/dsdt.dsl
OperationRegion (ERAM, SystemMemory, 0xFE0B0300, 0xFF)
Field (ERAM, ByteAcc, Lock, Preserve)
{
    Offset (0x10),
    LPBL, 1,  # bit 6: 电源灯控制
    ...
}

Method (SLT2, 1, Serialized)
{
    If ((L004 == One))  { LPBL = Zero }  # 开灯
    If ((L004 == Zero)) { LPBL = One  }  # 关灯
}
```

## 使用方法

### 基本命令

```bash
# 查看设备信息和当前状态
sudo python3 legion_power_light.py info

# 开启电源灯
sudo python3 legion_power_light.py on

# 关闭电源灯
sudo python3 legion_power_light.py off

# 切换状态
sudo python3 legion_power_light.py toggle

# 默认行为(无参数): 切换状态
sudo python3 legion_power_light.py
```

### 调试命令

```bash
# 转储 EC 寄存器(用于调试)
sudo python3 legion_power_light.py dump
```

输出示例:
```
EC 寄存器转储 (0x10-0x20):
偏移  值     二进制        描述
--------------------------------------------------
0x10  0x45  01000101 ← LPBL (电源灯)
0x11  0x00  00000000
...
```

## 集成到 HueSync

### ✅ 已集成方案 (推荐)

电源灯控制功能已通过 **Mixin 模式**集成到 HueSync 的设备类中:

```
py_modules/devices/
  ├── legion_power_led_mixin.py    # 电源灯控制 Mixin
  ├── legion_go.py                 # Legion Go (继承 Mixin)
  └── legion_go_tablet.py          # Legion Go S (继承 Mixin)
```

**使用方法:**

```python
from devices.legion_go import LegionGoLEDDevice
from devices.legion_go_tablet import LegionGoTabletLEDDevice

# 初始化设备 (自动检测电源灯支持)
device = LegionGoLEDDevice()  # 或 LegionGoTabletLEDDevice()

# 控制摇杆/平板灯 (现有功能)
device.set_color(mode=RGBMode.Solid, color=Color(255, 0, 0))

# 控制电源灯 (新功能)
device.set_power_light(True)   # 开灯
device.set_power_light(False)  # 关灯

# 查询电源灯状态
status = device.get_power_light()  # True/False/None
if status is not None:
    print(f"Power LED is {'ON' if status else 'OFF'}")
```

**在插件中集成:**

```python
# main.py
class Plugin:
    async def set_power_light(self, enabled: bool):
        """设置电源灯状态"""
        try:
            # 直接调用设备类的方法,无需 subprocess
            success = self.led_control.device.set_power_light(enabled)
            if success:
                logger.info(f"Power LED set to: {'ON' if enabled else 'OFF'}")
            return success
        except Exception as e:
            logger.error(f"Failed to set power light: {e}", exc_info=True)
            return False
    
    async def get_power_light(self):
        """获取电源灯状态"""
        try:
            status = self.led_control.device.get_power_light()
            return status
        except Exception as e:
            logger.error(f"Failed to get power light: {e}", exc_info=True)
            return None
```

**优势:**
- ✅ 零性能开销 - 无 subprocess 调用
- ✅ 代码复用 - 使用现有的 EC 类和 portio 库
- ✅ 自动检测 - 自动识别设备型号和 EC 配置
- ✅ 优雅降级 - 不支持的设备不影响主功能
- ✅ 统一管理 - 所有灯光控制在同一个设备类中

---

### 🔧 独立脚本方案 (备用)

如果需要在命令行独立使用,可以使用本目录下的 `legion_power_light.py` 脚本:

## 系统要求

- **操作系统**: Linux (SteamOS, Arch, Ubuntu 等)
- **Python**: 3.9+
- **权限**: root (需要访问 `/dev/port`)
- **设备**: Legion Go (83E1/83N0/83N1) 或 Legion Go S (83L3/83N6/83Q2/83Q3)

## 故障排查

### 错误: 无法打开 /dev/port

**原因**: 没有 root 权限

**解决**: 使用 `sudo` 运行脚本

### 错误: 无法识别设备型号

**原因**: DMI 信息不匹配或非 Legion Go 设备

**解决**: 
1. 检查产品型号: `cat /sys/devices/virtual/dmi/id/product_name`
2. 如果是 Legion Go 但型号不在列表中,修改脚本中的 `DEVICE_CONFIGS`

### 寄存器写入成功但灯不亮/不灭

**原因**: 可能寄存器偏移或位位置不正确

**解决**:
1. 运行 `sudo python3 legion_power_light.py dump` 查看寄存器值
2. 手动切换灯(如果有物理开关),再次转储对比差异
3. 更新 `DEVICE_CONFIGS` 中的配置

## 致谢

- [hhd-dev/hwinfo](https://github.com/hhd-dev/hwinfo) - ACPI DSDT 表数据来源
- [LegionGoRemapper](https://github.com/aarron-lee/LegionGoRemapper) - 启发和参考

## 许可证

MIT License

