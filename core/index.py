import json
from enum import *
from typing import *


class IndexType(Enum):
    """
    索引类型
    """

    FILE = 1
    DIR = 2


class Index:
    """
    目录索引项
    """

    def __init__(self, name: str, index: int, type: IndexType):
        self.index = index
        self.name = name
        self.type = type

    def getIndex(self):
        return self.index

    def getName(self):
        return self.name

    def getType(self):
        return self.type


class FileAssets:
    """
    文件资产
    """

    def __init__(self, size: int, blockNo: int):
        self.createTime = None
        self.modifyTime = None
        self.size = size
        self.blockNo = blockNo
        self.setChangeFile()

    def getCreateTime(self):
        return self.createTime

    def getModifyTime(self):
        return self.modifyTime

    def getSize(self):
        return self.size

    def getBlockNo(self):
        return self.blockNo

    def setChangeFile(self):
        # 自动计算？
        pass


class DIRAssets:
    """
    目录资产
    """

    def __init__(self, name: str):
        self.createTime = None
        self.size = None
        self.includes = [0] * 2

    def getCreateTime(self):
        return self.createTime

    def getSize(self):
        return self.size

    def setChangeFile(self):
        # 自动计算？
        pass


class IndexTreeNode:
    """
    文件树节点
    """

    def __init__(self, val: Index, parent=None):
        self.val = val
        self.children = []
        self.parent = None

    def getIndex(self):
        return self.val.getIndex()

    def getChildren(self):
        return self.children

    def extendchild(self, child):
        self.children.extend(child)
        child.parent = self

    def removeChild(self, child):
        self.children.remove(child)

    def getType(self) -> IndexType:
        return self.val.getType()

    def getPath(self):
        path = []
        node = self
        path = node.val.getName()
        while node.parent:
            node = node.parent
            path = node.val.getName() + "\\" + path
        return path


def indexTreeSerialize(root: IndexTreeNode) -> str:
    if not root:
        return None
    data = {"val": root.val.__dict__, "children": [], "parent": root.parent}
    for child in root.children:
        data["children"].append(indexTreeSerialize(child))
    return json.dumps(data)


def indexTreeDeserialize(data) -> IndexTreeNode:
    if not data:
        return None
    data = json.loads(data)
    root = IndexTreeNode(Index(**data["val"]), parent=data["parent"])
    for child in data["children"]:
        root.children.append(indexTreeDeserialize(child))
    return root
