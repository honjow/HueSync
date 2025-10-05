class IdInfo:
    def __init__(self, vid, pid):
        self.vid = vid
        self.pid = pid


ID_MAP = {
    # "ONEXPLAYER X1": IdInfo(0x1A2C, 0xB001),
    "ONEXPLAYER F1": IdInfo(0x1A2C, 0xB001),
    "ROG Ally RC71L": IdInfo(0x0B05, 0x1ABE),
    "ROG Ally X RC72L": IdInfo(0x0B05, 0x1B4C),
    # Legion Go (tablet mode, not Go S)
    "83E1": IdInfo(0x17EF, 0x6182),  # Legion Go
    "83N0": IdInfo(0x17EF, 0x6182),  # Legion Go 2
    "83N1": IdInfo(0x17EF, 0x6182),  # Legion Go 2
}
