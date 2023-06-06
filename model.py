from PyQt6 import QtCore, QtGui, QtWidgets


class FileSystemModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = FileSystemItem("", None)  # 创建根节点

        # 添加示例数据
        dir1 = FileSystemItem("dir1", self.root_item)
        file1 = FileSystemItem("file1.txt", dir1)
        dir2 = FileSystemItem("dir2", self.root_item)
        file2 = FileSystemItem("file2.jpg", dir2)
        dir3 = FileSystemItem("dir3", dir1)

    # 返回每个节点的父节点
    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item == self.root_item:
            return QtCore.QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    # 返回每个节点的子节点数目
    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return len(parent_item.children())

    # 返回每个节点的列数目
    def columnCount(self, parent):
        return 1

    def headerData(self, section, orientation, role):
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
            and section == 0
        ):
            return "文件系统根目录：.\\"
        return super().headerData(section, orientation, role)

    # 返回每个节点的数据
    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return item.data(index.column())

    # 根据索引返回节点
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QtCore.QModelIndex()


class FileSystemItem:
    def __init__(self, name, parent=None):
        self.item_name = name
        self.parent_item = parent
        self.child_items = []

        # 如果有父节点，把自己添加到父节点中
        if parent is not None:
            parent.addChild(self)

    # 添加子项
    def addChild(self, item):
        self.child_items.append(item)

    # 获取子项数目
    def childCount(self):
        return len(self.child_items)

    # 获取所有子项
    def children(self):
        return self.child_items

    # 获取指定子项
    def child(self, row):
        if row < len(self.child_items):
            return self.child_items[row]
        return None

    # 获取父项
    def parent(self):
        return self.parent_item

    # 获取数据
    def data(self, column):
        return self.item_name

    # 获取行号
    def row(self):
        if self.parent_item is not None:
            return self.parent_item.child_items.index(self)
        return 0
