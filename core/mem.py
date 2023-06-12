from .config import *
import os, struct, sys
from bitarray import *
from PyQt6.QtCore import *
from .index import *
from .file import *


class Memeory(QObject):
    """
    整个物理内存
    """

    def __init__(
        self,
        config: Config,
        isFile: bool = False,
    ) -> None:
        self.config = config
        self.size = self.config.BLOCK_SIZE * self.config.BLOCK_NUM
        self.memory = []
        self.bitmap: list[bitarray] = []
        # 假设第0块是存各种信息的索引块吧，然后位视图从第1块开始，索引从第2块开始
        self.infoMap = {
            "bitmap": 0,
            "index": 1,
        }
        self.occupyBlock = 0
        if isFile:
            pass
        else:
            self._creatNewMem()

    def _creatNewMem(self) -> None:
        for i in range(self.config.BLOCK_NUM):
            # 使用字节数组
            self.memory.append(bytearray(self.config.BLOCK_SIZE))
        # 创建位视图并且写入位视图
        # INFO 位视图是固定大小所以直接写入了，还有个索引是可大可小的，直接写入后面添加不方便，所以交给管理器管了！
        self.bitmap = bitarray(self.config.BLOCK_NUM)
        self.bitmap.setall(False)
        self.bitmap[0] = True
        self.inMem(bytearray(self.bitmap.tobytes()), self.infoMap["bitmap"])
        # 占位
        self.inMem(bytearray(0), self.infoMap["index"])

    def inMem(self, data: bytearray, blockNo: int = None) -> int:
        # 分解
        datas = []
        length = self.config.BLOCK_SIZE - BACK_NUM
        for i in range(0, len(data), length):
            temp = data[i : i + length]
            temp.extend((-1).to_bytes(INT_NUM, byteorder="little", signed=True))
            datas.append(temp)
        # 写入
        if blockNo is None:
            # 从位视图中找到空闲块
            # TODO 这个找是否可以使用扫描法优化？
            blockNo = self.bitmap.index(False)
        if self._inMem(datas, blockNo):
            return blockNo
        else:
            return None

    def _inMem(self, data: list[bytearray], blockNo: int) -> bool:
        # 先检查有没有剩余空间
        if len(data) > self.bitmap.count(False) - self.occupyBlock:
            return False
        self.bitmap[blockNo] = True
        for i in range(len(data)):
            index = -1
            if i != len(data) - 1:
                index = self.bitmap.index(False)
                self.bitmap[index] = True
            self.memory[blockNo][: len(data[i])] = data[i]
            self.memory[blockNo][-4:] = (index).to_bytes(
                INT_NUM, byteorder="little", signed=True
            )
            blockNo = index
        self.memory[blockNo][-4:] = (-1).to_bytes(
            INT_NUM, byteorder="little", signed=True
        )
        return True

    def checkMemBlock(self, size: int) -> bool:
        return size <= self.bitmap.count(False)

    def occupy(self, blockNum: int) -> bool:
        if self.checkMemBlock(blockNum):
            self.occupyBlock += blockNum
            return True
        else:
            return False

    def cancelOccupy(self, blockNum: int) -> None:
        self.occupyBlock -= blockNum

    def deleteMem(self, blockNo: int) -> None:
        if blockNo == None:
            return
        # 直接标记为可用
        self.bitmap[blockNo] = False
        address = int.from_bytes(
            self.memory[blockNo][-INT_NUM:], byteorder="little", signed=True
        )
        while address != -1:
            address = int.from_bytes(
                self.memory[blockNo][-INT_NUM:], byteorder="little", signed=True
            )
            self.bitmap[blockNo] = False

    def changeMem(self, data: bytearray, blockNo: int) -> int:
        filesize = self.getFileSize(blockNo)
        num = self.getBlockNum(data) - filesize // (self.config.BLOCK_SIZE - BACK_NUM)
        if num > 0:
            if not self.checkMemBlock(num):
                return False
        self.deleteMem(blockNo)
        self.inMem(data, blockNo)
        return True

    def getBlockNum(self, data: bytearray) -> int:
        return len(data) // (self.config.BLOCK_SIZE - BACK_NUM)

    def getFileSize(self, blockNo: int) -> int:
        size = 0
        size += self.config.BLOCK_SIZE - BACK_NUM
        blockNo = int(self.memory[blockNo][-4:], 2)
        while blockNo != -1:
            size += self.config.BLOCK_SIZE - BACK_NUM
            blockNo = int(self.memory[blockNo][-4:], 2)
        return size

    def getData(self, blockNo: int) -> bytearray:
        data = bytearray()
        if EOF in self.memory[blockNo]:
            data.extend(self.memory[blockNo][: self.memory[blockNo].index(EOF)])
        blockNo = int.from_bytes(
            self.memory[blockNo][-INT_NUM:], byteorder="little", signed=True
        )
        while blockNo != -1:
            data.extend(self.memory[blockNo][: self.memory[blockNo].index(EOF)])
            blockNo = int.from_bytes(
                self.memory[blockNo][-INT_NUM:], byteorder="little", signed=True
            )
        return data


class MemController(QObject):
    """
    内存管理器
    """

    noEnoughSignal = pyqtSignal()
    addDirSignal = pyqtSignal(str)

    def __init__(self, config: Config) -> None:
        self.config = config
        self.index = None
        self.root = None
        self.indexs: list[Index] = []
        self.indexNum = 0
        self.indexSize1 = 0
        self.indexSize2 = 0
        # 获取内存
        if os.path.exists(config.MEM_FILE):
            self.mem = Memeory(self.config, True)
        else:
            self.mem = Memeory(self.config, False)
            self.addIndex(None, ".", IndexType.DIR)

        # 读取内存中的位图
        # 读取内存中的索引表

    def getRoot(self) -> MyNode:
        return self.root

    def addFile(self, ini: MyNode, filename: str = "新建文件") -> str:
        i = 1
        name = filename
        while True and ini:
            name = filename if i == 1 else f"{filename}{i}"
            if not ini.hasChildName(name):
                break
            i += 1
        index = Index(name, self.indexNum, IndexType.FILE)
        self.indexs.append(index)
        node = MyNode(index, ini)
        self.indexNum += 1
        if not self.checkIndexSize():
            self.indexs.pop()
            self.indexNum -= 1
            self.noEnoughSignal.emit()
            return None
        else:
            if ini is not None:
                ini.appendChild(node)
            else:
                self.root = node
            return name

    def addIndex(self, ini: MyNode, name0: str, type: IndexType) -> str:
        name = None
        if name0 == None:
            if type == IndexType.FILE:
                name = "新建文件"
            elif type == IndexType.DIR:
                name = "新建文件夹"
            name0 = name
        i = 1
        name = name0
        while True and ini:
            name = name0 if i == 1 else f"{name0}{i}"
            if not ini.hasChildName(name):
                break
            i += 1
        index = Index(name, self.indexNum, type)
        self.indexs.append(index)
        node = MyNode(index, ini)
        self.indexNum += 1
        if not self.checkIndexSize():
            self.indexs.pop()
            self.indexNum -= 1
            self.noEnoughSignal.emit()
            return None
        else:
            if ini is not None:
                ini.appendChild(node)
            else:
                self.root = node
            return name

    def deleteNode(self, faNode: MyNode, node: MyNode) -> None:
        if node in faNode.children:
            faNode.children.remove(node)
            self.indexs.remove(node.index)
            if node.index.type == IndexType.DIR:
                pass
                for child in node.children:
                    self.deleteNode(node, child)
            else:
                self.mem.deleteMem(node.index.blockNo)

    def checkIndexSize(self) -> bool:
        if self.mem.checkMemBlock(1):
            return True
        else:
            return False

    def readFile(self, index: int) -> str:
        return self.mem.getData(index.blockNo).decode("utf-8")

    def writeFile(self, index, content: str, time: str) -> bool:
        if not self.checkIndexSize():
            self.noEnoughSignal.emit()
            return False
        if not self.mem.checkMemBlock(
            1 + self.mem.getBlockNum(bytearray(content.encode("utf-8")))
        ):
            self.noEnoughSignal.emit()
            return False
        if index.blockNo is not None:
            self.mem.deleteMem(index.blockNo)
        no = self.mem.inMem(bytearray(content.encode("utf-8")))
        index.blockNo = no
        index.size = len(content.encode("utf-8"))
        index.modifyTime = time
        return True

    def indexIn(self):
        self.mem.cancelOccupy(self.indexSize1 + self.indexSize2)
        if not self.mem.inMem(
            bytearray(indexTreeSerialize(self.index).encode("utf-8"))
        ):
            self.noEnoughSignal.emit()

    def getModel(self) -> MyModel:
        return MyModel(self.root)
