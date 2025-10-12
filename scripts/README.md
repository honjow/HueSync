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

## 集成到 Decky 插件

在 `main.py` 中添加电源灯控制方法:

```python
import subprocess

class Plugin:
    async def set_power_light(self, enabled: bool):
        """设置电源灯状态"""
        try:
            script_path = os.path.join(
                decky.DECKY_PLUGIN_DIR, 
                "scripts", 
                "legion_power_light.py"
            )
            cmd = ["python3", script_path, "on" if enabled else "off"]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"Power light set to: {'on' if enabled else 'off'}")
                return True
            else:
                logger.error(f"Failed to set power light: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(e, exc_info=True)
            return False
    
    async def get_power_light(self):
        """获取电源灯状态"""
        try:
            script_path = os.path.join(
                decky.DECKY_PLUGIN_DIR,
                "scripts",
                "legion_power_light.py"
            )
            cmd = ["python3", script_path, "info"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # 从输出中解析状态
                if "开启" in result.stdout:
                    return True
                elif "关闭" in result.stdout:
                    return False
            
            return None
            
        except Exception as e:
            logger.error(e, exc_info=True)
            return None
```

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

