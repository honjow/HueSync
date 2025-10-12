#!/usr/bin/env python3
"""
Legion Go / Legion Go S 电源灯控制
自动检测设备型号并使用正确的寄存器

使用方法:
    sudo python3 legion_power_light.py [command]

命令:
    on, enable   - 开启电源灯
    off, disable - 关闭电源灯
    toggle       - 切换电源灯状态
    info         - 显示当前状态
    dump         - 转储 EC 寄存器(调试)

无需 acpi_call 模块,直接通过 EC 端口访问
适用于 SteamOS 等只读文件系统
"""

import os
import time

class LegionPowerLightController:
    """
    Legion Go 系列电源灯控制器
    自动检测设备型号(Go 或 Go S)并使用对应的寄存器
    """
    
    EC_DATA_PORT = 0x62
    EC_CMD_PORT = 0x66
    EC_CMD_READ = 0x80
    EC_CMD_WRITE = 0x81
    EC_IBF = 0x02  # Input Buffer Full
    EC_OBF = 0x01  # Output Buffer Full
    
    # 设备配置
    DEVICE_CONFIGS = {
        # Legion Go (原版) - 型号: 83E1, 83N0, 83N1
        "legion_go": {
            "models": ["83E1", "83N0", "83N1"],
            "register_offset": 0x52,  # EC 寄存器偏移
            "bit_position": 5,        # 位位置
            "field_name": "LEDP",
        },
        # Legion Go S - 型号: 83L3, 83N6, 83Q2, 83Q3
        "legion_go_s": {
            "models": ["83L3", "83N6", "83Q2", "83Q3"],
            "register_offset": 0x10,  # EC 寄存器偏移
            "bit_position": 6,        # 位位置
            "field_name": "LPBL",
        },
    }
    
    def __init__(self):
        if os.geteuid() != 0:
            raise PermissionError("需要 root 权限")
        
        # 检测设备型号
        self.device_type = self._detect_device()
        if not self.device_type:
            raise RuntimeError("无法识别设备型号,不支持的 Legion Go 设备")
        
        # 获取设备配置
        self.config = self.DEVICE_CONFIGS[self.device_type]
        self.register_offset = self.config["register_offset"]
        self.bit_position = self.config["bit_position"]
        self.bit_mask = 1 << self.bit_position
        self.field_name = self.config["field_name"]
        
        # 打开 /dev/port
        try:
            self.port_fd = os.open("/dev/port", os.O_RDWR)
        except Exception as e:
            raise RuntimeError(f"无法打开 /dev/port: {e}")
        
        print(f"✓ 检测到设备: {self.device_type.upper().replace('_', ' ')}")
        print(f"  产品型号: {self.product_name}")
        print(f"  寄存器配置: {self.field_name} @ 0x{self.register_offset:02X}[bit {self.bit_position}]")
        print(f"  逻辑: 反向 (bit=0开灯, bit=1关灯)")
    
    def __del__(self):
        if hasattr(self, 'port_fd'):
            try:
                os.close(self.port_fd)
            except:
                pass
    
    def _detect_device(self) -> str | None:
        """
        检测设备型号
        从 DMI 信息中读取产品名称
        """
        dmi_paths = [
            "/sys/devices/virtual/dmi/id/product_name",
            "/sys/class/dmi/id/product_name",
        ]
        
        for dmi_path in dmi_paths:
            try:
                with open(dmi_path, "r") as f:
                    product_name = f.read().strip()
                    self.product_name = product_name
                    
                    # 检查是否匹配已知型号
                    for device_type, config in self.DEVICE_CONFIGS.items():
                        if product_name in config["models"]:
                            return device_type
                    
                    # 如果没有精确匹配,尝试模糊匹配
                    if "83E1" in product_name or "83N0" in product_name or "83N1" in product_name:
                        return "legion_go"
                    elif "83L3" in product_name or "83N6" in product_name or "83Q" in product_name:
                        return "legion_go_s"
                    
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"警告: 读取 DMI 信息失败: {e}")
                continue
        
        return None
    
    def outb(self, value: int, port: int):
        """写入字节到 I/O 端口"""
        os.lseek(self.port_fd, port, os.SEEK_SET)
        os.write(self.port_fd, bytes([value]))
    
    def inb(self, port: int) -> int:
        """从 I/O 端口读取字节"""
        os.lseek(self.port_fd, port, os.SEEK_SET)
        data = os.read(self.port_fd, 1)
        return data[0] if data else 0
    
    def _wait_ibf_clear(self, timeout=10000):
        """等待 Input Buffer 清空"""
        for _ in range(timeout):
            if not (self.inb(self.EC_CMD_PORT) & self.EC_IBF):
                return True
            time.sleep(0.00001)
        return False
    
    def _wait_obf_set(self, timeout=10000):
        """等待 Output Buffer 有数据"""
        for _ in range(timeout):
            if self.inb(self.EC_CMD_PORT) & self.EC_OBF:
                return True
            time.sleep(0.00001)
        return False
    
    def read_ec(self, offset: int) -> int:
        """读取 EC 寄存器"""
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy (IBF)")
        
        self.outb(self.EC_CMD_READ, self.EC_CMD_PORT)
        
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy after read cmd")
        
        self.outb(offset, self.EC_DATA_PORT)
        
        if not self._wait_obf_set():
            raise TimeoutError("EC timeout waiting data")
        
        return self.inb(self.EC_DATA_PORT)
    
    def write_ec(self, offset: int, value: int):
        """写入 EC 寄存器"""
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy (IBF)")
        
        self.outb(self.EC_CMD_WRITE, self.EC_CMD_PORT)
        
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy after write cmd")
        
        self.outb(offset, self.EC_DATA_PORT)
        
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy after addr")
        
        self.outb(value, self.EC_DATA_PORT)
        
        if not self._wait_ibf_clear():
            raise TimeoutError("EC busy after data")
    
    def set_power_light(self, enabled: bool) -> bool:
        """
        设置电源灯状态
        
        Args:
            enabled: True=开灯, False=关灯
        
        Returns:
            bool: 是否成功
        """
        try:
            current = self.read_ec(self.register_offset)
            print(f"当前 EC[0x{self.register_offset:02X}] = 0x{current:02X} ({current:08b})")
            
            # 两种设备都是反向逻辑: bit=0 开灯, bit=1 关灯
            if enabled:
                new_value = current & ~self.bit_mask  # 清除位 = 开灯
            else:
                new_value = current | self.bit_mask   # 设置位 = 关灯
            
            print(f"写入值: 0x{new_value:02X} ({new_value:08b})")
            
            self.write_ec(self.register_offset, new_value)
            time.sleep(0.05)
            
            verify = self.read_ec(self.register_offset)
            print(f"验证值: 0x{verify:02X} ({verify:08b})")
            
            return verify == new_value
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_power_light(self) -> bool | None:
        """
        获取当前电源灯状态
        
        Returns:
            bool: True=开灯, False=关灯, None=读取失败
        """
        try:
            current = self.read_ec(self.register_offset)
            bit_value = (current & self.bit_mask) >> self.bit_position
            
            # 反向逻辑: bit=0 表示开灯
            return bit_value == 0
                
        except Exception as e:
            print(f"错误: {e}")
            return None
    
    def dump_ec_registers(self, start=None, end=None):
        """转储 EC 寄存器用于调试"""
        if start is None:
            # 自动选择合适的范围
            start = (self.register_offset // 0x10) * 0x10
            end = start + 0x10
        
        print(f"\nEC 寄存器转储 (0x{start:02X}-0x{end:02X}):")
        print("偏移  值     二进制        描述")
        print("-" * 50)
        
        for offset in range(start, end):
            try:
                value = self.read_ec(offset)
                marker = f" ← {self.field_name} (电源灯)" if offset == self.register_offset else ""
                print(f"0x{offset:02X}  0x{value:02X}  {value:08b}{marker}")
            except Exception as e:
                print(f"0x{offset:02X}  读取失败: {e}")


def main():
    import sys
    
    if os.geteuid() != 0:
        print("❌ 需要 root 权限运行")
        print("   请使用: sudo python3 legion_power_light.py [command]")
        sys.exit(1)
    
    try:
        controller = LegionPowerLightController()
        
        # 处理命令行参数
        if len(sys.argv) > 1:
            cmd = sys.argv[1].lower()
            
            if cmd == "dump":
                controller.dump_ec_registers()
                sys.exit(0)
            elif cmd == "info":
                current = controller.get_power_light()
                if current is not None:
                    print(f"\n当前电源灯状态: {'🔆 开启' if current else '🔅 关闭'}")
                sys.exit(0)
            elif cmd in ["on", "enable"]:
                success = controller.set_power_light(True)
                print("\n✅ 已开启电源灯" if success else "\n❌ 开启失败")
                sys.exit(0 if success else 1)
            elif cmd in ["off", "disable"]:
                success = controller.set_power_light(False)
                print("\n✅ 已关闭电源灯" if success else "\n❌ 关闭失败")
                sys.exit(0 if success else 1)
            elif cmd == "toggle":
                current = controller.get_power_light()
                if current is None:
                    print("\n❌ 无法读取当前状态")
                    sys.exit(1)
                
                new_state = not current
                success = controller.set_power_light(new_state)
                print(f"\n✅ 已切换到: {'🔆 开启' if new_state else '🔅 关闭'}" if success else "\n❌ 切换失败")
                sys.exit(0 if success else 1)
            else:
                print(f"❌ 未知命令: {cmd}")
                print("\n用法: sudo python3 legion_power_light.py [command]")
                print("\n命令:")
                print("  on, enable   - 开启电源灯")
                print("  off, disable - 关闭电源灯")
                print("  toggle       - 切换电源灯状态")
                print("  info         - 显示当前状态")
                print("  dump         - 转储 EC 寄存器(调试)")
                sys.exit(1)
        else:
            # 默认行为: 切换状态
            current = controller.get_power_light()
            if current is None:
                print("\n❌ 无法读取当前状态")
                sys.exit(1)
            
            print(f"\n当前状态: {'🔆 开启' if current else '🔅 关闭'}")
            
            new_state = not current
            success = controller.set_power_light(new_state)
            print(f"\n✅ 已切换到: {'🔆 开启' if new_state else '🔅 关闭'}" if success else "\n❌ 切换失败")
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

