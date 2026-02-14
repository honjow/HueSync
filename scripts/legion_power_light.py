#!/usr/bin/env python3
"""
Legion Go / Legion Go S 电源灯控制
Power LED Control with Multi-Backend Fallback

支持多后端自动降级。
Multi-backend support with automatic fallback.

使用方法 | Usage:
    sudo python3 legion_power_light.py [命令] [选项]
    sudo python3 legion_power_light.py [command] [options]

命令 | Commands:
    on, enable   - 开启电源灯 | Turn on power LED
    off, disable - 关闭电源灯 | Turn off power LED
    toggle       - 切换电源灯状态 | Toggle power LED state
    info         - 显示当前状态和后端信息 | Show current status and backend info
    dump         - 转储 EC 寄存器 (仅 ec_port 后端) | Dump EC registers (ec_port only)
    backends     - 列出所有后端及其可用性 | List all backends and their availability

选项 | Options:
    --backend <name>  - 强制使用指定后端 | Force a specific backend
                        (acpi_call, mmio, ec_port)

后端优先级 (自动选择) | Backend priority (auto):
    1. acpi_call  - 通过 /proc/acpi/call 调用 WMI (最兼容新 BIOS)
    2. mmio       - 通过 /dev/mem 内存映射 I/O
    3. ec_port    - 通过 /dev/port EC I/O 端口命令 (传统方式)
"""

import mmap
import os
import subprocess
import sys
import time


# ============================================================
# 设备配置 | Device configuration
# ============================================================

DEVICE_CONFIGS = {
    # Legion Go (原版) - 型号: 83E1, 83N0, 83N1
    "legion_go": {
        "models": ["83E1", "83N0", "83N1"],
        "register_offset": 0x52,  # EC 寄存器偏移 (LEDP)
        "bit_position": 5,        # 位位置
        "field_name": "LEDP",
    },
    # Legion Go S - 型号: 83L3, 83N6, 83Q2, 83Q3
    "legion_go_s": {
        "models": ["83L3", "83N6", "83Q2", "83Q3"],
        "register_offset": 0x10,  # EC 寄存器偏移 (LPBL)
        "bit_position": 6,        # 位位置
        "field_name": "LPBL",
    },
}

# 公共常量 | Common constants
WMI_PATH = r"\_SB.GZFD.WMAF"       # WMI 方法路径 (Go 和 Go S 一致)
WMI_LIGHTING_ID = 0x04              # Lighting_ID (Go 和 Go S 一致)
ECMM_BASE = 0xFE0B0300              # ECMM/ERAM 基地址 (Go 和 Go S 一致)
ECMM_SIZE = 0xFF


# ============================================================
# 后端实现 (独立，不依赖 py_modules)
# Backend implementations (standalone, no dependency on py_modules)
# ============================================================


class AcpiCallBackend:
    """
    通过 acpi_call 内核模块调用 WMI 方法的后端。
    Backend using acpi_call kernel module.

    WMI 命令格式:
        设置: \\_SB.GZFD.WMAF 0 0x02 {lighting_id, 0x00, brightness}
              brightness=0x02 → 开灯(LEDP=0), brightness=0x01 → 关灯(LEDP=1)
        获取: \\_SB.GZFD.WMAF 0 0x01 lighting_id
              返回 buffer, byte 1: 0x02=亮, 0x01=灭
    """

    name = "acpi_call"
    ACPI_CALL_PATH = "/proc/acpi/call"

    def __init__(self, lighting_id: int):
        self._lighting_id = lighting_id

    def is_available(self) -> bool:
        """检查 acpi_call 是否可用，不可用则尝试加载。"""
        if os.path.exists(self.ACPI_CALL_PATH):
            return True
        try:
            result = subprocess.run(
                ["modprobe", "acpi_call"], capture_output=True, timeout=5
            )
            return result.returncode == 0 and os.path.exists(self.ACPI_CALL_PATH)
        except Exception:
            return False

    def _acpi_call(self, command: str) -> str | None:
        """执行 ACPI 调用并返回结果。"""
        try:
            with open(self.ACPI_CALL_PATH, "w") as f:
                f.write(command)
            with open(self.ACPI_CALL_PATH, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"  acpi_call 错误: {e}")
            return None

    def set_power_led(self, enabled: bool) -> bool:
        """设置电源灯状态。"""
        # brightness=0x02 → 开灯, brightness=0x01 → 关灯
        brightness = 0x02 if enabled else 0x01
        cmd = (
            f"{WMI_PATH} 0 0x02 "
            f"{{0x{self._lighting_id:02X}, 0x00, 0x{brightness:02X}}}"
        )
        print(f"  acpi_call 命令: {cmd}")
        result = self._acpi_call(cmd)
        if result is None:
            return False
        print(f"  响应: {result}")

        # 回读验证
        current = self.get_power_led()
        return current == enabled

    def get_power_led(self) -> bool | None:
        """获取电源灯当前状态。"""
        cmd = f"{WMI_PATH} 0 0x01 0x{self._lighting_id:02X}"
        result = self._acpi_call(cmd)
        if result is None:
            return None
        try:
            # 解析响应: acpi_call 返回 "0x00020000..." 或 "{0x01, 0x02}" 格式
            # byte 1: 0x02=亮, 0x01=灭
            cleaned = result.strip("\x00").strip()
            if cleaned.startswith("{"):
                # 解析逗号分隔格式: {0x01, 0x02}
                parts = cleaned.strip("{}").split(",")
                if len(parts) >= 2:
                    state_byte = int(parts[1].strip(), 0)
                    return state_byte == 0x02
            elif cleaned.startswith("0x"):
                # 解析十六进制值 (小端序 buffer)
                val = int(cleaned, 16)
                state_byte = (val >> 8) & 0xFF
                return state_byte == 0x02
            print(f"  未知响应格式: {cleaned}")
            return None
        except Exception as e:
            print(f"  解析错误: {e}, 原始数据: {result}")
            return None


class MMIOBackend:
    """
    通过 /dev/mem 内存映射 I/O 的后端。
    Backend using memory-mapped I/O via /dev/mem.

    直接通过 ECMM/ERAM SystemMemory 区域访问 EC 寄存器。
    基地址 0xFE0B0300，反向逻辑: bit=0 开灯, bit=1 关灯。
    """

    name = "mmio"

    def __init__(self, offset: int, bit: int):
        self._offset = offset
        self._bit = bit
        self._bit_mask = 1 << bit
        self._fd = None
        self._mm = None
        self._page_offset = 0

    def _ensure_mapped(self) -> bool:
        """确保 /dev/mem 已打开并映射。"""
        if self._mm is not None:
            return True
        try:
            # mmap 需要页对齐
            page_size = mmap.PAGESIZE
            self._page_offset = ECMM_BASE % page_size
            map_base = ECMM_BASE - self._page_offset
            map_size = self._page_offset + ECMM_SIZE
            self._fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            self._mm = mmap.mmap(
                self._fd, map_size, mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE, offset=map_base,
            )
            return True
        except Exception as e:
            print(f"  mmio 映射错误: {e}")
            self._cleanup()
            return False

    def _cleanup(self):
        """释放 mmap 和文件描述符。"""
        if self._mm:
            try:
                self._mm.close()
            except Exception:
                pass
            self._mm = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

    def is_available(self) -> bool:
        """检查 /dev/mem 是否可访问。"""
        if not os.path.exists("/dev/mem"):
            return False
        if not self._ensure_mapped():
            return False
        try:
            _ = self._mm[self._page_offset + self._offset]
            return True
        except Exception:
            self._cleanup()
            return False

    def set_power_led(self, enabled: bool) -> bool:
        """通过 MMIO 设置电源灯状态。"""
        if not self._ensure_mapped():
            return False
        try:
            addr = self._page_offset + self._offset
            current = self._mm[addr]
            print(f"  mmio 读取 0x{ECMM_BASE + self._offset:08X} = 0x{current:02X} ({current:08b})")

            # 反向逻辑: bit=0 开灯, bit=1 关灯
            if enabled:
                new_value = current & ~self._bit_mask  # 清除位 = 开灯
            else:
                new_value = current | self._bit_mask   # 设置位 = 关灯

            print(f"  mmio 写入 0x{new_value:02X} ({new_value:08b})")
            self._mm[addr] = new_value
            time.sleep(0.01)

            # 验证写入
            verify = self._mm[addr]
            print(f"  mmio 验证 0x{verify:02X} ({verify:08b})")
            return (verify & self._bit_mask) == (new_value & self._bit_mask)
        except Exception as e:
            print(f"  mmio 错误: {e}")
            return False

    def get_power_led(self) -> bool | None:
        """通过 MMIO 获取电源灯状态。"""
        if not self._ensure_mapped():
            return None
        try:
            current = self._mm[self._page_offset + self._offset]
            bit_value = (current >> self._bit) & 1
            return bit_value == 0  # 反向逻辑: bit=0 表示亮
        except Exception:
            return None


class ECPortBackend:
    """
    通过 EC I/O 端口命令的后端 (传统方式)。
    Backend using EC I/O port commands via /dev/port (legacy).

    通过端口 0x66（命令/状态）和 0x62（数据），
    使用标准 EC 读取 (0x80) 和写入 (0x81) 命令通信。
    反向逻辑: bit=0 开灯, bit=1 关灯。
    """

    name = "ec_port"

    EC_DATA_PORT = 0x62    # 数据端口
    EC_CMD_PORT = 0x66     # 命令/状态端口
    EC_CMD_READ = 0x80     # EC 读取命令
    EC_CMD_WRITE = 0x81    # EC 写入命令
    EC_IBF = 0x02          # Input Buffer Full
    EC_OBF = 0x01          # Output Buffer Full

    def __init__(self, offset: int, bit: int):
        self._offset = offset
        self._bit = bit
        self._bit_mask = 1 << bit
        self._port_fd = None

    def _ensure_port(self) -> bool:
        """确保 /dev/port 已打开。"""
        if self._port_fd is not None:
            return True
        try:
            self._port_fd = os.open("/dev/port", os.O_RDWR)
            return True
        except Exception as e:
            print(f"  ec_port 打开错误: {e}")
            return False

    def _outb(self, value: int, port: int):
        """写入字节到 I/O 端口。"""
        os.lseek(self._port_fd, port, os.SEEK_SET)
        os.write(self._port_fd, bytes([value]))

    def _inb(self, port: int) -> int:
        """从 I/O 端口读取字节。"""
        os.lseek(self._port_fd, port, os.SEEK_SET)
        data = os.read(self._port_fd, 1)
        return data[0] if data else 0

    def _wait_ibf_clear(self, timeout=10000):
        """等待 Input Buffer 清空。"""
        for _ in range(timeout):
            if not (self._inb(self.EC_CMD_PORT) & self.EC_IBF):
                return True
            time.sleep(0.00001)
        return False

    def _wait_obf_set(self, timeout=10000):
        """等待 Output Buffer 有数据。"""
        for _ in range(timeout):
            if self._inb(self.EC_CMD_PORT) & self.EC_OBF:
                return True
            time.sleep(0.00001)
        return False

    def read_ec(self, offset: int) -> int:
        """读取 EC 寄存器。"""
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (IBF)")
        self._outb(self.EC_CMD_READ, self.EC_CMD_PORT)
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (读取命令后)")
        self._outb(offset, self.EC_DATA_PORT)
        if not self._wait_obf_set():
            raise TimeoutError("EC 超时 (等待数据)")
        return self._inb(self.EC_DATA_PORT)

    def write_ec(self, offset: int, value: int):
        """写入 EC 寄存器。"""
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (IBF)")
        self._outb(self.EC_CMD_WRITE, self.EC_CMD_PORT)
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (写入命令后)")
        self._outb(offset, self.EC_DATA_PORT)
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (地址发送后)")
        self._outb(value, self.EC_DATA_PORT)
        if not self._wait_ibf_clear():
            raise TimeoutError("EC 忙 (数据发送后)")

    def is_available(self) -> bool:
        """检查 EC I/O 端口是否可访问。"""
        if not os.path.exists("/dev/port"):
            return False
        if not self._ensure_port():
            return False
        try:
            self.read_ec(self._offset)
            return True
        except Exception:
            return False

    def set_power_led(self, enabled: bool) -> bool:
        """通过 EC I/O 端口设置电源灯状态。"""
        if not self._ensure_port():
            return False
        try:
            current = self.read_ec(self._offset)
            print(f"  ec_port 读取 EC[0x{self._offset:02X}] = 0x{current:02X} ({current:08b})")

            # 反向逻辑: bit=0 开灯, bit=1 关灯
            if enabled:
                new_value = current & ~self._bit_mask  # 清除位 = 开灯
            else:
                new_value = current | self._bit_mask   # 设置位 = 关灯

            print(f"  ec_port 写入 0x{new_value:02X} ({new_value:08b})")
            self.write_ec(self._offset, new_value)
            time.sleep(0.05)

            # 验证写入
            verify = self.read_ec(self._offset)
            print(f"  ec_port 验证 0x{verify:02X} ({verify:08b})")
            return (verify & self._bit_mask) == (new_value & self._bit_mask)
        except Exception as e:
            print(f"  ec_port 错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_power_led(self) -> bool | None:
        """通过 EC I/O 端口获取电源灯状态。"""
        if not self._ensure_port():
            return None
        try:
            current = self.read_ec(self._offset)
            bit_value = (current >> self._bit) & 1
            return bit_value == 0  # 反向逻辑: bit=0 表示亮
        except Exception:
            return None

    def dump_registers(self, field_name: str, start: int = None, end: int = None):
        """转储 EC 寄存器用于调试。"""
        if not self._ensure_port():
            print("  无法访问 /dev/port")
            return
        if start is None:
            start = (self._offset // 0x10) * 0x10
            end = start + 0x10

        print(f"\nEC 寄存器转储 (0x{start:02X}-0x{end - 1:02X}):")
        print("偏移    值       二进制        描述")
        print("-" * 55)
        for offset in range(start, end):
            try:
                value = self.read_ec(offset)
                marker = f" ← {field_name} (电源灯)" if offset == self._offset else ""
                print(f"0x{offset:02X}    0x{value:02X}     {value:08b}{marker}")
            except Exception as e:
                print(f"0x{offset:02X}    读取失败: {e}")


# ============================================================
# 设备检测 | Device detection
# ============================================================


def detect_device() -> tuple[str, dict] | None:
    """
    从 DMI 信息中检测设备型号。
    Detect device model from DMI info.
    """
    dmi_paths = [
        "/sys/devices/virtual/dmi/id/product_name",
        "/sys/class/dmi/id/product_name",
    ]
    for dmi_path in dmi_paths:
        try:
            with open(dmi_path, "r") as f:
                product_name = f.read().strip()

            # 精确匹配 | Exact match
            for device_type, config in DEVICE_CONFIGS.items():
                if product_name in config["models"]:
                    return device_type, {**config, "product_name": product_name}

            # 模糊匹配 | Fuzzy match
            if any(m in product_name for m in ["83E1", "83N0", "83N1"]):
                cfg = DEVICE_CONFIGS["legion_go"]
                return "legion_go", {**cfg, "product_name": product_name}
            elif any(m in product_name for m in ["83L3", "83N6", "83Q"]):
                cfg = DEVICE_CONFIGS["legion_go_s"]
                return "legion_go_s", {**cfg, "product_name": product_name}
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"警告: 读取 DMI 信息失败: {e}")
    return None


# ============================================================
# 后端选择 | Backend selection
# ============================================================


def create_backends(offset: int, bit: int) -> list:
    """按优先级顺序创建所有后端。"""
    return [
        AcpiCallBackend(lighting_id=WMI_LIGHTING_ID),
        MMIOBackend(offset=offset, bit=bit),
        ECPortBackend(offset=offset, bit=bit),
    ]


def select_backend(offset: int, bit: int, forced: str | None = None):
    """
    选择最佳可用后端，支持自动降级。
    Select best available backend with fallback.
    """
    backends = create_backends(offset, bit)

    # 强制指定模式 | Forced mode
    if forced:
        for b in backends:
            if b.name == forced:
                if b.is_available():
                    return b
                else:
                    print(f"强制指定的后端 '{forced}' 不可用")
                    return None
        print(f"未知后端: {forced}")
        print(f"可用后端: {', '.join(b.name for b in backends)}")
        return None

    # 自动选择: 按优先级依次尝试 | Auto-select: try each in priority order
    for b in backends:
        try:
            if b.is_available():
                return b
        except Exception:
            continue
    return None


# ============================================================
# 主程序 | Main
# ============================================================


def print_usage():
    print("用法: sudo python3 legion_power_light.py [命令] [选项]")
    print()
    print("命令:")
    print("  on, enable   - 开启电源灯")
    print("  off, disable - 关闭电源灯")
    print("  toggle       - 切换电源灯状态")
    print("  info         - 显示当前状态和后端信息")
    print("  dump         - 转储 EC 寄存器 (仅 ec_port 后端)")
    print("  backends     - 列出所有后端及其可用性")
    print()
    print("选项:")
    print("  --backend <名称>  - 强制使用指定后端 (acpi_call, mmio, ec_port)")


def main():
    if os.geteuid() != 0:
        print("❌ 需要 root 权限运行")
        print("   请使用: sudo python3 legion_power_light.py [命令]")
        sys.exit(1)

    # 解析命令行参数 | Parse arguments
    args = sys.argv[1:]
    forced_backend = None
    cmd = None

    i = 0
    while i < len(args):
        if args[i] == "--backend" and i + 1 < len(args):
            forced_backend = args[i + 1]
            i += 2
        elif cmd is None:
            cmd = args[i].lower()
            i += 1
        else:
            i += 1

    # 检测设备 | Detect device
    result = detect_device()
    if result is None:
        print("❌ 无法识别设备型号，不支持的 Legion Go 设备")
        sys.exit(1)

    device_type, config = result
    offset = config["register_offset"]
    bit = config["bit_position"]
    field_name = config["field_name"]

    print(f"✓ 检测到设备: {device_type.upper().replace('_', ' ')}")
    print(f"  产品型号: {config['product_name']}")
    print(f"  寄存器配置: {field_name} @ EC[0x{offset:02X}] bit {bit}")
    print("  逻辑: 反向 (bit=0 开灯, bit=1 关灯)")

    # 在选择后端前处理 'backends' 命令 | Handle 'backends' command before backend selection
    if cmd == "backends":
        print("\n后端可用性:")
        backends = create_backends(offset, bit)
        for idx, b in enumerate(backends, 1):
            try:
                available = b.is_available()
                status = "✓ 可用" if available else "✗ 不可用"
            except Exception as e:
                status = f"✗ 错误: {e}"
            priority = "(最高优先级)" if idx == 1 else "(最低优先级)" if idx == len(backends) else ""
            print(f"  {idx}. {b.name:12s} - {status} {priority}")
        sys.exit(0)

    # 选择后端 | Select backend
    backend = select_backend(offset, bit, forced=forced_backend)
    if backend is None:
        print("\n❌ 没有可用的后端")
        print("   请运行: sudo python3 legion_power_light.py backends")
        sys.exit(1)

    forced_str = " (强制指定)" if forced_backend else " (自动选择)"
    print(f"  后端: {backend.name}{forced_str}")

    # 执行命令 | Execute command
    if cmd == "dump":
        if isinstance(backend, ECPortBackend):
            backend.dump_registers(field_name)
        else:
            print("\n注意: dump 仅支持 ec_port 后端")
            print(f"当前后端: {backend.name}")
            print("请使用: --backend ec_port dump")
        sys.exit(0)

    elif cmd == "info":
        current = backend.get_power_led()
        if current is not None:
            print(f"\n当前电源灯状态: {'🔆 开启' if current else '🔅 关闭'}")
        else:
            print("\n❌ 无法读取电源灯状态")
        sys.exit(0)

    elif cmd in ["on", "enable"]:
        success = backend.set_power_led(True)
        print(f"\n{'✅ 已开启电源灯' if success else '❌ 开启失败'}")
        sys.exit(0 if success else 1)

    elif cmd in ["off", "disable"]:
        success = backend.set_power_led(False)
        print(f"\n{'✅ 已关闭电源灯' if success else '❌ 关闭失败'}")
        sys.exit(0 if success else 1)

    elif cmd == "toggle" or cmd is None:
        current = backend.get_power_led()
        if current is None:
            print("\n❌ 无法读取当前状态")
            sys.exit(1)
        print(f"\n当前状态: {'🔆 开启' if current else '🔅 关闭'}")
        new_state = not current
        success = backend.set_power_led(new_state)
        if success:
            print(f"✅ 已切换到: {'🔆 开启' if new_state else '🔅 关闭'}")
        else:
            print("❌ 切换失败")
        sys.exit(0 if success else 1)

    else:
        print(f"\n❌ 未知命令: {cmd}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
