"""
Power LED Backend Abstraction Layer
电源灯后端抽象层

Provides multiple backends for controlling Legion Go power LED with automatic fallback.
为 Legion Go 电源灯控制提供多后端自动降级支持。

Priority order | 优先级顺序:
1. AcpiCallBackend  - Uses /proc/acpi/call (WMAF WMI method) | 通过 acpi_call 调用 WMI 方法
2. MMIOBackend      - Uses /dev/mem memory-mapped I/O | 通过 /dev/mem 内存映射 I/O
3. ECPortBackend    - Uses EC I/O port commands (0x66/0x62) | 通过 EC I/O 端口命令

Author: HueSync Team
License: MIT
"""

import logging
import mmap
import os
import subprocess
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class PowerLEDBackend(ABC):
    """
    Abstract base class for power LED access backends.
    电源灯访问后端的抽象基类。

    Each backend provides a different hardware access path to control
    the Legion Go series power LED.
    每个后端提供不同的硬件访问路径来控制 Legion Go 系列的电源灯。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name for logging. | 用于日志的后端名称。"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this backend is usable on current system.
        检查该后端在当前系统上是否可用。
        Should not raise exceptions. | 不应抛出异常。
        """
        ...

    @abstractmethod
    def set_power_led(self, enabled: bool) -> bool:
        """
        Set power LED state. | 设置电源灯状态。

        Args:
            enabled: True to turn on, False to turn off | True 开灯, False 关灯

        Returns:
            True if successful | 成功返回 True
        """
        ...

    @abstractmethod
    def get_power_led(self) -> bool | None:
        """
        Get current power LED state. | 获取当前电源灯状态。

        Returns:
            True if on, False if off, None on error
            True 表示亮, False 表示灭, None 表示出错
        """
        ...

    def close(self) -> None:
        """Release any resources held by this backend. | 释放后端持有的资源。"""
        pass


class AcpiCallBackend(PowerLEDBackend):
    """
    Backend using acpi_call kernel module to invoke WMAF WMI method.
    通过 acpi_call 内核模块调用联想 WMAF WMI 方法的后端。

    This is the official ACPI interface provided by Lenovo.
    这是联想提供的官方 ACPI 接口。

    WMI command format | WMI 命令格式:
        Set | 设置: \\_SB.GZFD.WMAF 0 0x02 {lighting_id, 0x00, brightness}
             brightness=0x02 → ON (LEDP/LPBL=0), brightness=0x01 → OFF (LEDP/LPBL=1)
        Get | 获取: \\_SB.GZFD.WMAF 0 0x01 lighting_id
             Returns buffer where byte 1: 0x02=ON, 0x01=OFF
             返回 buffer，其中 byte 1: 0x02=亮, 0x01=灭
    """

    ACPI_CALL_PATH = "/proc/acpi/call"
    WMI_PATH = r"\_SB.GZFD.WMAF"

    def __init__(self, lighting_id: int = 0x04):
        self._lighting_id = lighting_id

    @property
    def name(self) -> str:
        return "acpi_call"

    def is_available(self) -> bool:
        """Check if acpi_call is loaded, try to load it if not.
        检查 acpi_call 是否已加载，未加载则尝试加载。"""
        if os.path.exists(self.ACPI_CALL_PATH):
            logger.debug("acpi_call module already loaded")
            return True

        # Try to load the module | 尝试加载模块
        try:
            result = subprocess.run(
                ["modprobe", "acpi_call"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0 and os.path.exists(self.ACPI_CALL_PATH):
                logger.info("acpi_call module loaded successfully")
                return True
            logger.debug(
                f"modprobe acpi_call failed: rc={result.returncode}, "
                f"stderr={result.stderr.decode().strip()}"
            )
        except FileNotFoundError:
            logger.debug("modprobe command not found")
        except subprocess.TimeoutExpired:
            logger.debug("modprobe acpi_call timed out")
        except Exception as e:
            logger.debug(f"Failed to load acpi_call: {e}")

        return False

    def _acpi_call(self, command: str) -> str | None:
        """
        Execute an ACPI call and return the result.
        执行 ACPI 调用并返回结果。

        Args:
            command: ACPI call string | ACPI 调用命令字符串

        Returns:
            Response string or None on error | 响应字符串或 None（出错时）
        """
        try:
            with open(self.ACPI_CALL_PATH, "w") as f:
                f.write(command)
            with open(self.ACPI_CALL_PATH, "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"acpi_call failed for '{command}': {e}")
            return None

    def set_power_led(self, enabled: bool) -> bool:
        # brightness=0x02 → ON (LEDP=0), brightness=0x01 → OFF (LEDP=1)
        # brightness=0x02 → 开灯 (LEDP=0), brightness=0x01 → 关灯 (LEDP=1)
        brightness = 0x02 if enabled else 0x01
        cmd = (
            f"{self.WMI_PATH} 0 0x02 "
            f"{{0x{self._lighting_id:02X}, 0x00, 0x{brightness:02X}}}"
        )
        logger.debug(f"acpi_call set: {cmd}")
        result = self._acpi_call(cmd)
        if result is None:
            return False

        # Verify by reading back | 回读验证
        current = self.get_power_led()
        success = current == enabled
        if success:
            logger.debug(f"Power LED set to {'ON' if enabled else 'OFF'} via acpi_call")
        else:
            logger.warning(
                f"Power LED verification failed via acpi_call: "
                f"expected {'ON' if enabled else 'OFF'}, got {current}"
            )
        return success

    def get_power_led(self) -> bool | None:
        cmd = f"{self.WMI_PATH} 0 0x01 0x{self._lighting_id:02X}"
        result = self._acpi_call(cmd)
        if result is None:
            return None

        try:
            # Response format | 响应格式: {byte0, byte1, ...} or hex values
            # byte1: 0x02=ON(亮), 0x01=OFF(灭)
            # Parse the response | 解析响应
            # acpi_call returns hex like "0x00020000..." or "{0x01, 0x02}"
            cleaned = result.strip("\x00").strip()
            if cleaned.startswith("{"):
                # Parse comma-separated format | 解析逗号分隔格式: {0x01, 0x02}
                parts = cleaned.strip("{}").split(",")
                if len(parts) >= 2:
                    state_byte = int(parts[1].strip(), 0)
                    is_on = state_byte == 0x02
                    logger.debug(
                        f"Power LED status via acpi_call: "
                        f"{'ON' if is_on else 'OFF'} (raw={cleaned})"
                    )
                    return is_on
            elif cleaned.startswith("0x"):
                # Parse single hex value (little-endian buffer as int)
                # 解析单个十六进制值（小端序 buffer 转 int）
                val = int(cleaned, 16)
                # byte 0 is low byte, byte 1 is next
                # byte 0 是低字节, byte 1 是下一个
                state_byte = (val >> 8) & 0xFF
                is_on = state_byte == 0x02
                logger.debug(
                    f"Power LED status via acpi_call: "
                    f"{'ON' if is_on else 'OFF'} (raw={cleaned})"
                )
                return is_on

            logger.warning(f"Unexpected acpi_call response format: {cleaned}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse acpi_call response '{result}': {e}")
            return None


class MMIOBackend(PowerLEDBackend):
    """
    Backend using memory-mapped I/O via /dev/mem.
    通过 /dev/mem 内存映射 I/O 的后端。

    Directly accesses the EC register through the ECMM/ERAM SystemMemory region.
    通过 ECMM/ERAM SystemMemory 区域直接访问 EC 寄存器。

    ECMM/ERAM base address | 基地址: 0xFE0B0300 (same for Legion Go and Go S | Go 和 Go S 一致)
    Uses inverted logic | 使用反向逻辑: bit=0 means ON(亮), bit=1 means OFF(灭)
    """

    ECMM_BASE = 0xFE0B0300
    ECMM_SIZE = 0xFF

    def __init__(self, offset: int, bit: int):
        self._offset = offset
        self._bit = bit
        self._bit_mask = 1 << bit
        self._fd = None
        self._mm = None
        self._page_offset = 0

    @property
    def name(self) -> str:
        return "mmio"

    def _ensure_mapped(self) -> bool:
        """Ensure /dev/mem is opened and mapped. Returns True on success.
        确保 /dev/mem 已打开并映射。成功返回 True。"""
        if self._mm is not None:
            return True

        try:
            # mmap requires page alignment | mmap 需要页对齐
            page_size = mmap.PAGESIZE
            self._page_offset = self.ECMM_BASE % page_size
            map_base = self.ECMM_BASE - self._page_offset
            map_size = self._page_offset + self.ECMM_SIZE

            self._fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
            self._mm = mmap.mmap(
                self._fd,
                map_size,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=map_base,
            )
            logger.debug(
                f"MMIO mapped: base=0x{self.ECMM_BASE:08X}, "
                f"page_offset=0x{self._page_offset:X}, map_base=0x{map_base:08X}"
            )
            return True
        except Exception as e:
            logger.debug(f"Failed to mmap /dev/mem: {e}")
            self._cleanup()
            return False

    def _cleanup(self):
        """Release mmap and file descriptor. | 释放 mmap 和文件描述符。"""
        if self._mm is not None:
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
        """Try to map /dev/mem and read the target register.
        尝试映射 /dev/mem 并读取目标寄存器。"""
        if not os.path.exists("/dev/mem"):
            logger.debug("/dev/mem not found")
            return False

        if not self._ensure_mapped():
            return False

        try:
            # Verify we can read the register | 验证能否读取寄存器
            _ = self._mm[self._page_offset + self._offset]
            logger.debug(
                f"MMIO read test OK: offset=0x{self._offset:02X}, "
                f"addr=0x{self.ECMM_BASE + self._offset:08X}"
            )
            return True
        except Exception as e:
            logger.debug(f"MMIO read test failed: {e}")
            self._cleanup()
            return False

    def set_power_led(self, enabled: bool) -> bool:
        if not self._ensure_mapped():
            return False

        try:
            addr = self._page_offset + self._offset
            current = self._mm[addr]

            # Inverted logic | 反向逻辑: bit=0 → ON(亮), bit=1 → OFF(灭)
            if enabled:
                new_value = current & ~self._bit_mask  # Clear bit = ON | 清除位 = 开灯
            else:
                new_value = current | self._bit_mask  # Set bit = OFF | 设置位 = 关灯

            self._mm[addr] = new_value

            # Verify | 验证写入
            verify = self._mm[addr]
            success = (verify & self._bit_mask) == (new_value & self._bit_mask)

            if success:
                logger.debug(
                    f"Power LED set to {'ON' if enabled else 'OFF'} via MMIO: "
                    f"addr=0x{self.ECMM_BASE + self._offset:08X}, "
                    f"bit={self._bit}, old=0x{current:02X}, "
                    f"new=0x{new_value:02X}, verify=0x{verify:02X}"
                )
            else:
                logger.warning(
                    f"MMIO write verification failed: "
                    f"expected 0x{new_value:02X}, got 0x{verify:02X}"
                )
            return success
        except Exception as e:
            logger.error(f"MMIO set_power_led failed: {e}", exc_info=True)
            return False

    def get_power_led(self) -> bool | None:
        if not self._ensure_mapped():
            return None

        try:
            addr = self._page_offset + self._offset
            current = self._mm[addr]
            bit_value = (current >> self._bit) & 1

            # Inverted logic | 反向逻辑: bit=0 means ON(亮)
            is_on = bit_value == 0
            logger.debug(
                f"Power LED status via MMIO: {'ON' if is_on else 'OFF'} "
                f"(addr=0x{self.ECMM_BASE + self._offset:08X}, "
                f"register=0x{current:02X}, bit{self._bit}={bit_value})"
            )
            return is_on
        except Exception as e:
            logger.error(f"MMIO get_power_led failed: {e}", exc_info=True)
            return None

    def close(self) -> None:
        self._cleanup()


class ECPortBackend(PowerLEDBackend):
    """
    Backend using EC I/O port commands (legacy method).
    通过 EC I/O 端口命令的后端（传统方式）。

    Communicates via ports 0x66 (command/status) and 0x62 (data)
    using standard EC read (0x80) and write (0x81) commands.
    通过端口 0x66（命令/状态）和 0x62（数据），
    使用标准 EC 读取 (0x80) 和写入 (0x81) 命令通信。

    Uses inverted logic | 使用反向逻辑: bit=0 means ON(亮), bit=1 means OFF(灭)
    """

    def __init__(self, offset: int, bit: int):
        self._offset = offset
        self._bit = bit
        self._bit_mask = 1 << bit

    @property
    def name(self) -> str:
        return "ec_port"

    def is_available(self) -> bool:
        """Try to read the EC register via I/O port.
        尝试通过 I/O 端口读取 EC 寄存器。"""
        try:
            from ec import EC

            EC.Read(self._offset)
            logger.debug(f"EC port read test OK: offset=0x{self._offset:02X}")
            return True
        except Exception as e:
            logger.debug(f"EC port not available: {e}")
            return False

    def set_power_led(self, enabled: bool) -> bool:
        try:
            from ec import EC

            # Read current register value | 读取当前寄存器值
            current = EC.Read(self._offset)

            # Inverted logic | 反向逻辑: bit=0 → ON(亮), bit=1 → OFF(灭)
            if enabled:
                new_value = current & ~self._bit_mask  # Clear bit = ON | 清除位 = 开灯
            else:
                new_value = current | self._bit_mask  # Set bit = OFF | 设置位 = 关灯

            # Write new value | 写入新值
            EC.Write(self._offset, new_value)

            # Verify | 验证写入
            verify = EC.Read(self._offset)
            success = (verify & self._bit_mask) == (new_value & self._bit_mask)

            if success:
                logger.debug(
                    f"Power LED set to {'ON' if enabled else 'OFF'} via EC port: "
                    f"offset=0x{self._offset:02X}, bit={self._bit}, "
                    f"old=0x{current:02X}, new=0x{new_value:02X}, verify=0x{verify:02X}"
                )
            else:
                logger.warning(
                    f"EC port write verification failed: "
                    f"expected bit {'0' if enabled else '1'}, got 0x{verify:02X}"
                )
            return success
        except Exception as e:
            logger.error(f"EC port set_power_led failed: {e}", exc_info=True)
            return False

    def get_power_led(self) -> bool | None:
        try:
            from ec import EC

            # Read current register value | 读取当前寄存器值
            current = EC.Read(self._offset)
            bit_value = (current >> self._bit) & 1

            # Inverted logic | 反向逻辑: bit=0 means ON(亮)
            is_on = bit_value == 0
            logger.debug(
                f"Power LED status via EC port: {'ON' if is_on else 'OFF'} "
                f"(offset=0x{self._offset:02X}, register=0x{current:02X}, "
                f"bit{self._bit}={bit_value})"
            )
            return is_on
        except Exception as e:
            logger.error(f"EC port get_power_led failed: {e}", exc_info=True)
            return None


def select_backend(
    offset: int,
    bit: int,
    lighting_id: int = 0x04,
    forced_backend: str | None = None,
) -> PowerLEDBackend | None:
    """
    Select the best available power LED backend with automatic fallback.
    自动选择最佳可用的电源灯后端，支持自动降级。

    Priority | 优先级: acpi_call → MMIO → EC port

    Args:
        offset: EC register offset (e.g. 0x52 for Go, 0x10 for Go S)
                EC 寄存器偏移 (Go 用 0x52, Go S 用 0x10)
        bit: Bit position within the register (e.g. 5 for Go, 6 for Go S)
             寄存器内的位位置 (Go 用 5, Go S 用 6)
        lighting_id: WMI Lighting_ID for acpi_call backend (default 0x04)
                     acpi_call 后端使用的 WMI Lighting_ID (默认 0x04)
        forced_backend: Force a specific backend ("acpi_call", "mmio", "ec_port")
                        强制指定后端名称

    Returns:
        Selected backend instance, or None if all backends failed
        选中的后端实例，全部失败时返回 None
    """
    backends = [
        AcpiCallBackend(lighting_id=lighting_id),
        MMIOBackend(offset=offset, bit=bit),
        ECPortBackend(offset=offset, bit=bit),
    ]

    # Forced mode | 强制指定模式
    if forced_backend:
        for backend in backends:
            if backend.name == forced_backend:
                if backend.is_available():
                    logger.info(f"Power LED backend forced: {backend.name}")
                    return backend
                else:
                    logger.warning(
                        f"Forced backend '{forced_backend}' is not available"
                    )
                    return None
        logger.warning(f"Unknown backend name: {forced_backend}")
        return None

    # Auto-select: try each in priority order | 自动选择: 按优先级依次尝试
    for backend in backends:
        try:
            if backend.is_available():
                logger.info(f"Power LED backend selected: {backend.name}")
                return backend
            logger.debug(f"Power LED backend '{backend.name}' not available, trying next")
        except Exception as e:
            logger.debug(f"Power LED backend '{backend.name}' check failed: {e}")

    logger.warning("No power LED backend available")
    return None
