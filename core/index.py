import json
from enum import *
from typing import *
from PyQt6.QtCore import *


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
        self.modifyTime = None
        self.size = None
        self.blockNo = None


class MyNode:
    def __init__(self, index: Index, parent=None):
        self.index = index
        self.name = self.index.name
        self.parent = parent
        self.children = []
        self.isVisible = False
        if self.index.type == IndexType.DIR:
            self.isVisible = True

    def appendChild(self, child):
        self.children.append(child)

    def childAtRow(self, row):
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]

    def childCount(self):
        return sum(child.isVisible for child in self.children)  # 只返回可见子节点的数量

    def rowOfChild(self, child):
        if not child.isVisible:
            return -1  # 如果子节点不可见，则返回-1
        return self.children.index(child)

    def getParent(self):
        return self.parent

    def hasChildName(self, name: str):
        for child in self.children:
            if child.name == name:
                return True
        return False

    def getChildByName(self, name: str):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def getPath(self):
        # 如果当前节点是根节点，直接返回根节点的名称
        if self.parent is None:
            return self.name

        # 递归获取父节点的路径，并将当前节点的名称添加到路径中
        parent_path = self.parent.getPath()
        return parent_path + "\\" + self.name


class MyModel(QAbstractItemModel):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self.rootNode = root

    def headerData(self, section, orientation, role):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return "磁盘根目录：.\\"
        return super().headerData(section, orientation, role)

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return node.name

        return None

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentNode = parent.internalPointer() if parent.isValid() else self.rootNode

        # 遍历可见子节点来寻找第row个可见子节点
        visibleRow = -1
        for childNode in parentNode.children:
            if not childNode.isVisible:
                continue  # 如果该子节点不可见，则跳过
            visibleRow += 1
            if visibleRow == row:
                return self.createIndex(row, column, childNode)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childNode = index.internalPointer()
        parentNode = childNode.parent
        if parentNode == self.rootNode:
            return QModelIndex()
        return self.createIndex(parentNode.rowOfChild(childNode), 0, parentNode)

    def rowCount(self, parent):
        parentNode = parent.internalPointer() if parent.isValid() else self.rootNode
        return sum(child.isVisible for child in parentNode.children)  # 只算可见子节点的数量
