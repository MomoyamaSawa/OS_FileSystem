BLOCK_SIZE = 512
BLOCK_NUM = 48
BACK_NUM = 8
INT_NUM = 4
EOF = b"\xff\xff\xff\xff"
MEM_FILE = "mem.data"


class Config:
    def __init__(self):
        self.BLOCK_SIZE = BLOCK_SIZE
        self.BLOCK_NUM = BLOCK_NUM
        self.MEM_FILE = MEM_FILE
