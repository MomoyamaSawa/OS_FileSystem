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
            "bitmap": 1,
            "index": 2,
        }
        self.occupyBlock = 0
        if isFile:
            pass
        else:
            self._creatNewMem()

    def _creatNewMem(self, file: str) -> None:
        for i in range(self.config.BLOCK_NUM):
            # 使用字节数组
            self.memory.append(bytearray(self.config.BLOCK_SIZE))
        # 创建位视图并且写入位视图
        # INFO 位视图是固定大小所以直接写入了，还有个索引是可大可小的，直接写入后面添加不方便，所以交给管理器管了！
        self.bitmap = bitarray(self.config.BLOCK_NUM)
        self.bitmap.setall(False)
        self.bitmap[0] = True
        self.inMem(bytearray(self.bitmap.tobytes()), self.infoMap["bitmap"])

    def inMem(self, data: bytearray, blockNo: int = None) -> int:
        # 分解
        datas = [
            data[i : i + self.config.BLOCK_SIZE - 2 * sys.getsizeof(int)]
            for i in range(
                0, len(data), self.config.BLOCK_SIZE - 2 * sys.getsizeof(int)
            )
        ]
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
            data[i].extend(
                (index).to_bytes(sys.getsizeof(int), byteorder="little", signed=True)
            )
            self.memory[blockNo] = data[i]
            blockNo = index
        self.memory[blockNo][-4:] = (-1).to_bytes()
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

    def deleteMem(self, blockNo: int) -> bool:
        # 直接标记为可用
        self.bitmap[blockNo] = False
        while int(self.memory[blockNo][-4:], 2) != -1:
            blockNo = int(self.memory[blockNo][-4:], 2)
            self.bitmap[blockNo] = False

    def changeMem(self, data: bytearray, blockNo: int) -> int:
        filesize = self.getFileSize(blockNo)
        num = self.getBlockNum(data) - filesize // (
            self.config.BLOCK_SIZE - 2 * sys.getsizeof(int)
        )
        if num > 0:
            if not self.checkMemBlock(num):
                return False
        self.deleteMem(blockNo)
        self.inMem(data, blockNo)
        return True

    def getBlockNum(self, data: bytearray) -> int:
        return len(data) // (self.config.BLOCK_SIZE - 2 * sys.getsizeof(int))

    def getFileSize(self, blockNo: int) -> int:
        size = 0
        size += self.config.BLOCK_SIZE - 2 * sys.getsizeof(int)
        blockNo = int(self.memory[blockNo][-4:], 2)
        while blockNo != -1:
            size += self.config.BLOCK_SIZE - 2 * sys.getsizeof(int)
            blockNo = int(self.memory[blockNo][-4:], 2)
        return size


class MemController(QObject):
    """
    内存管理器
    """

    noEnoughSignal = pyqtSignal()

    def __init__(self, config: Config) -> None:
        self.config = config
        self.index = None
        self.indexs: list[Union[FileAssets, DIRAssets]] = []
        self.indexNum = 0
        self.indexSize1 = 0
        self.indexSize2 = 0
        # 获取内存
        if os.path.exists(config.MEM_FILE):
            self.mem = Memeory(self.config, True)
        else:
            self.mem = Memeory(self.config, False)
            self.addDir(None, ".")
        # 读取内存中的位图
        # 读取内存中的索引表

    def getRoot(self) -> IndexTreeNode:
        return self.index

    def addFile(self, ini: IndexTreeNode, file: File) -> None:
        no = self.mem.inMem(bytearray(file.getContent().encode("utf-8")))
        if no is None:
            self.noEnoughSignal.emit()
            return
        self.indexs.append(FileAssets(len(file.getContent().encode("utf-8")), no))
        index = IndexTreeNode(Index(file.getName(), self.indexNum, IndexType.FILE))
        self.indexNum += 1
        ini.extendchild(index)
        if not self._checkIndexSize():
            self.mem.deleteMem(no)
            self.indexs.pop()
            self.indexNum -= 1
            ini.removeChild(index)
            self.noEnoughSignal.emit()

    def addDir(self, ini: IndexTreeNode, dirName: str) -> None:
        self.indexs.append(DIRAssets(dirName))
        index = IndexTreeNode(Index(dirName, self.indexNum, IndexType.DIR))
        self.indexNum += 1
        if ini is None:
            ini.extendchild(index)
        if not self._checkIndexSize():
            self.indexs.pop()
            self.indexNum -= 1
            ini.removeChild(index)
            self.noEnoughSignal.emit()

    def _checkIndexSize(self) -> None:
        byte_count1 = len(indexTreeSerialize(self.index).encode("utf-8"))
        byte_count2 = len(json.dumps(self.indexs).encode("utf-8"))
        no1 = False
        if (
            byte_count1
            > self.indexSize1
            * (self.config.BLOCK_SIZE - 2 * sys.getsizeof(int))
            * self.config.BLOCK_NUM
        ):
            if self.mem.occupy(1):
                self.indexSize1 += 1
            else:
                self.noEnoughSignal.emit()
        if (
            byte_count2
            > self.indexSize2
            * (self.config.BLOCK_SIZE - 2 * sys.getsizeof(int))
            * self.config.BLOCK_NUM
        ):
            if self.mem.occupy(1):
                self.indexSize2 += 1
            else:
                if no1:
                    self.mem.cancelOccupy(1)
                    self.indexSize1 -= 1
                self.noEnoughSignal.emit()
        if (
            byte_count1
            <= (self.indexSize1 - 1)
            * (self.config.BLOCK_SIZE - 2 * sys.getsizeof(int))
            * self.config.BLOCK_NUM
        ):
            self.mem.cancelOccupy(1)
        if (
            byte_count2
            <= (self.indexSize2 - 1)
            * (self.config.BLOCK_SIZE - 2 * sys.getsizeof(int))
            * self.config.BLOCK_NUM
        ):
            self.mem.cancelOccupy(1)

    def indexIn(self):
        self.mem.cancelOccupy(self.indexSize1 + self.indexSize2)
        if not self.mem.inMem(
            bytearray(indexTreeSerialize(self.index).encode("utf-8"))
        ):
            self.noEnoughSignal.emit()
