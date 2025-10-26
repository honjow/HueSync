import time

import portio
from config import logger

EC_IBF_BIT = 0b10
EC_OBF_BIT = 0b01
EC_CMD_STATUS_REGISTER_PORT = 0x66
EC_DATA_REGISTER_PORT = 0x62

RD_EC = 0x80  # Read Embedded Controller
WR_EC = 0x81  # Write Embedded Controller


def inb(port):
    return portio.inb(port)


def outb(port, data):
    return portio.outb(data, port)


# Use iopl(3) to get complete I/O permissions, not just ioperm for specific ports | 使用iopl(3)获得完整I/O权限，而不是只针对特定端口的ioperm
status = portio.iopl(3)
if status != 0:
    raise Exception("iopl error")


class EC:
    class Register:
        @staticmethod
        def WaitInputNFull():
            while EC.Register.GetStatus() & EC_IBF_BIT != 0:
                time.sleep(0.001)
                pass

        @staticmethod
        def WaitOutputFull():
            i = 0
            while EC.Register.GetStatus() & EC_OBF_BIT == 0:
                if i == 0xFFFF:
                    break
                i += 1

        @staticmethod
        def GetStatus():
            time.sleep(0.001)
            return inb(EC_CMD_STATUS_REGISTER_PORT)

        @staticmethod
        def SetCmd(cmd: int):
            EC.Register.WaitInputNFull()
            outb(EC_CMD_STATUS_REGISTER_PORT, cmd)

        @staticmethod
        def SetData(data: int):
            EC.Register.WaitInputNFull()
            outb(EC_DATA_REGISTER_PORT, data)

        @staticmethod
        def GetData():
            EC.Register.WaitOutputFull()
            return inb(EC_DATA_REGISTER_PORT)

    @staticmethod
    def Read(address: int):
        EC.Register.SetCmd(RD_EC)
        EC.Register.SetData(address)
        return EC.Register.GetData()

    @staticmethod
    def ReadLonger(address: int, length: int):
        sum = 0
        for len in range(length):
            EC.Register.SetCmd(RD_EC)
            EC.Register.SetData(address + len)
            sum = (sum << 8) + EC.Register.GetData()
        return sum

    @staticmethod
    def Write(address: int, data: int):
        EC.Register.SetCmd(WR_EC)
        EC.Register.SetData(address)
        EC.Register.SetData(data)
    
    @staticmethod
    def WriteFast(address: int, data: int):
        """Fast write without sleep delays - for batch operations only"""
        # Inline fast wait without sleep
        while inb(EC_CMD_STATUS_REGISTER_PORT) & EC_IBF_BIT != 0:
            pass  # Busy wait
        outb(EC_CMD_STATUS_REGISTER_PORT, WR_EC)
        
        while inb(EC_CMD_STATUS_REGISTER_PORT) & EC_IBF_BIT != 0:
            pass
        outb(EC_DATA_REGISTER_PORT, address)
        
        while inb(EC_CMD_STATUS_REGISTER_PORT) & EC_IBF_BIT != 0:
            pass
        outb(EC_DATA_REGISTER_PORT, data)

    @staticmethod
    def RamWrite(reg_addr: int, reg_data: int, address: int, data: int):
        high_byte = (address >> 8) & 0xFF
        low_byte = address & 0xFF
        portio.outb(0x2E, reg_addr)
        portio.outb(0x11, reg_data)
        portio.outb(0x2F, reg_addr)
        portio.outb(high_byte, reg_data)

        portio.outb(0x2E, reg_addr)
        portio.outb(0x10, reg_data)
        portio.outb(0x2F, reg_addr)
        portio.outb(low_byte, reg_data)

        portio.outb(0x2E, reg_addr)
        portio.outb(0x12, reg_data)
        portio.outb(0x2F, reg_addr)
        portio.outb(data, reg_data)
        # logger.debug(
        #     f"ECRamWrite high_byte={hex(high_byte)} low_byte={hex(low_byte)} address:{hex(address)} value:{data}"
        # )

    @staticmethod
    def RamRead(reg_addr: int, reg_data: int, address: int):
        high_byte = (address >> 8) & 0xFF
        low_byte = address & 0xFF
        portio.outb(0x2E, reg_addr)
        portio.outb(0x11, reg_data)
        portio.outb(0x2F, reg_addr)
        portio.outb(high_byte, reg_data)

        portio.outb(0x2E, reg_addr)
        portio.outb(0x10, reg_data)
        portio.outb(0x2F, reg_addr)
        portio.outb(low_byte, reg_data)

        portio.outb(0x2E, reg_addr)
        portio.outb(0x12, reg_data)
        portio.outb(0x2F, reg_addr)
        data = portio.inb(reg_data)
        logger.debug(
            f"ECRamRead high_byte={hex(high_byte)} low_byte={hex(low_byte)} address:{hex(address)} value:{data}"
        )
        return data

    @staticmethod
    def RamReadLonger(reg_addr: int, reg_data: int, address: int, length: int):
        sum = 0
        for len in range(length):
            value = EC.RamRead(reg_addr, reg_data, address + len)
            sum = (sum << 8) + value
            # logger.debug(f"count={len} sum={sum} address={address+len} value={value}")
        logger.debug(f"ECReadLonger  address:{hex(address)} value:{sum}")
        return sum

    def PrintAll():
        print("", "\t", end="")
        for z in range(0xF + 1):
            print(hex(z), "\t", end="")
        print()
        for x in range(0xF + 1):
            for y in range(0xF + 1):
                if y == 0x00:
                    print(hex(x), "\t", end="")
                print(EC.Read((x << 4) + y), "\t", end="")
            print()
