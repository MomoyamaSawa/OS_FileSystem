from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import copy, sys
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import *
from setting import *
from qfluentwidgets import FluentIcon as FIF
from model import *
from core.config import *
from core.mem import *
from core.file import *
from tool import *


class Slider(QWidget):
    """
    侧边栏
    """

    homeSignal = pyqtSignal()
    backSignal = pyqtSignal()
    resetSignal = pyqtSignal()
    changeSignal = pyqtSignal(MyNode)

    def __init__(self, model: MyModel, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedWidth(SLIDER_WIDTH)

        self.vLayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()
        self.containner = QFrame(self)

        self.homeButton = PrimaryToolButton(FIF.HOME, self)
        self.homeButton.clicked.connect(self.homeSignal.emit)
        self.backButton = PrimaryToolButton(FIF.CARE_LEFT_SOLID, self)
        self.backButton.clicked.connect(self.backSignal.emit)
        self.resetButton = PrimaryToolButton(FIF.SYNC, self)
        self.resetButton.clicked.connect(self.resetSignal.emit)

        self.view = TreeView(self)
        # 连接 clicked 信号到响应槽函数
        self.view.clicked.connect(self.on_tree_view_clicked)
        self.view.setModel(model)

        self._initLayout()

    def on_tree_view_clicked(self, index: QModelIndex):
        # 处理 TreeView 的 clicked 信号
        item = self.view.model().itemFromIndex(index)
        if item:
            self.changeSignal.emit(item)

    def _initLayout(self):
        self.setLayout(self.vLayout)
        self.containner.setLayout(self.hLayout)

        self.hLayout.addWidget(self.homeButton)
        self.hLayout.addWidget(self.backButton)
        self.hLayout.addWidget(self.resetButton)

        self.vLayout.addWidget(self.containner)
        self.vLayout.addSpacing(20)
        self.vLayout.addWidget(self.view)

    def _initQss(self):
        pass

    def updateModel(self):
        self.view.reset()

    def reset(self, model: MyModel):
        self.view.setModel(model)


class Card(QFrame):
    clicked = pyqtSignal()
    doubleClickSignal = pyqtSignal(str)
    menuSignal = pyqtSignal(str)
    delSignal = pyqtSignal(str)
    changeNameSignal = pyqtSignal(str, QFrame)
    copySignal = pyqtSignal(str)

    def __init__(self, type: IndexType, name: str, parent=None):
        super().__init__(parent)

        # 设置卡片的固定大小
        self.setFixedSize(CARD_SIZE[0], CARD_SIZE[1])

        # 文件图片
        self.icon_label = QLabel(self)
        if type == IndexType.DIR:
            pixmap = QPixmap(RESOURCE["floder"])
        else:
            pixmap = QPixmap(RESOURCE["file"])
        self.icon_label.setPixmap(pixmap.scaledToWidth(CARD_SIZE[1] // 2))

        # 文件名
        self.name_label = QLabel(name, self)
        self.name_label.installEventFilter(
            ToolTipFilter(self.name_label, showDelay=500)
        )
        self.name_label.setToolTip(name)
        self.name_label.setToolTipDuration(2000)

        # 布局
        self.vLayout = QVBoxLayout(self)

        self._initQss()
        self._initLayout()

    def _initLayout(self):
        self.vLayout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vLayout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.vLayout.setContentsMargins(10, 10, 10, 10)
        self.vLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _initQss(self):
        self.name_label.setStyleSheet(f"font-size: {FONT_SIZE}px")
        # 设置鼠标悬停时的样式
        self.setStyleSheet(
            f"""
            Card:hover {{
                background: rgba{NORMAL_COLOR_RGBA3};
                border-radius: {RADIUS}px;
            }}
        """
        )

    def mouseReleaseEvent(self, e):
        self.clicked.emit()
        # 要在上一级来设置这个背景色
        # self.setStyleSheet("Card { background: black } ")

    def mouseDoubleClickEvent(self, e):
        self.doubleClickSignal.emit(self.name_label.text())

    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)

        # add actions
        actionOpen = Action(FIF.SEND_FILL, "Open")
        actionOpen.triggered.connect(
            lambda: self.doubleClickSignal.emit(self.name_label.text())
        )
        menu.addAction(actionOpen)

        # add actions
        actionMenu = Action(FIF.SETTING, "Propertiy")
        actionMenu.triggered.connect(
            lambda: self.menuSignal.emit(self.name_label.text())
        )
        actionDelete = Action(FIF.DELETE, "Delete")
        actionDelete.triggered.connect(self.delete)
        actionChangeName = Action(FIF.EDIT, "Change Name")
        actionChangeName.triggered.connect(
            lambda: self.changeNameSignal.emit(self.name_label.text(), self)
        )
        actionCopy = Action(FIF.COPY, "Copy")
        actionCopy.triggered.connect(
            lambda: self.copySignal.emit(self.name_label.text())
        )
        actionCut = Action(FIF.CUT, "Cut")
        actionCut.triggered.connect(self.cut)
        menu.addActions(
            [
                actionCut,
                actionCopy,
                actionDelete,
                actionMenu,
                actionChangeName,
            ]
        )

        # show menu
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def cut(self):
        self.copySignal.emit(self.name_label.text())
        self.delete()

    def delete(self):
        theLayout = self.parent().layout()
        index = theLayout.indexOf(self)
        theLayout.takeAt(index)
        self.deleteLater()
        self.delSignal.emit(self.name_label.text())


class View(QWidget):
    """
    视图
    """

    addDirSignal = pyqtSignal()
    addFileSignal = pyqtSignal()
    inDirSignal = pyqtSignal(str)
    openFileSignal = pyqtSignal(str)
    menuSignal = pyqtSignal(str)
    delSignal = pyqtSignal(str)
    changeNameSignal = pyqtSignal(str, QFrame)
    proSignal = pyqtSignal()
    copySignal = pyqtSignal(str)
    pasteSignal = pyqtSignal()

    def __init__(self, root: MyNode, parent: QWidget = None):
        super().__init__(parent)

        self.vLayout = QVBoxLayout()

        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("请在此输入搜索内容")
        self.roundWidget = RoundWidget(self)
        self.scrollArea = SmoothScrollArea(self.roundWidget)
        self.scrolWidget = QWidget(self.scrollArea)
        self.scrollArea.setWidget(self.scrolWidget)
        self.scrollArea.setViewportMargins(0, 5, 0, 5)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.flowLayout = FlowLayout(self.scrolWidget, isTight=True, needAni=True)
        # customize animation
        self.flowLayout.setAnimation(250, QEasingCurve.Type.OutQuad)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(lambda: self.flowLayout.update())
        self.timer.start()

        self._initQss()
        self._initLayout()
        self.reset(root)

    def _initLayout(self):
        self.setLayout(self.vLayout)

        self.flowLayout.setContentsMargins(10, 10, 10, 10)
        self.flowLayout.setVerticalSpacing(20)
        self.flowLayout.setHorizontalSpacing(10)

        self.vLayout.addSpacing(8)
        self.vLayout.addWidget(self.searchBar)
        self.vLayout.addSpacing(20)
        self.vLayout.addWidget(self.roundWidget)

        self.roundWidget.setLayout(QVBoxLayout())
        self.roundWidget.layout().addWidget(self.scrollArea)
        self.scrolWidget.setLayout(self.flowLayout)

    def _initQss(self):
        self.scrollArea.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )
        self.scrolWidget.setStyleSheet(f"QWidget {{ background-color: transparent; }}")

    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)

        # add actions
        actionPaste = Action(FIF.PASTE, "Paste")
        actionPaste.triggered.connect(self.pasteSignal.emit)
        menu.addAction(actionPaste)

        # add sub menu
        submenu = RoundMenu("Sort", self)
        submenu.setIcon(FIF.SCROLL)
        submenu.addActions(
            [
                Action(FIF.VIDEO, "sort1"),
                Action(FIF.MUSIC, "sort2"),
            ]
        )
        menu.addMenu(submenu)

        submenu = RoundMenu("New", self)
        submenu.setIcon(FIF.ADD)
        actionDir = Action(FIF.FOLDER, "dir")
        actionDir.triggered.connect(self.addDirSignal.emit)
        actionFile = Action(FIF.DOCUMENT, "file")
        actionFile.triggered.connect(self.addFileSignal.emit)
        submenu.addActions(
            [
                actionDir,
                actionFile,
            ]
        )
        menu.addMenu(submenu)

        # add actions
        actionPro = Action(FIF.SETTING, "Propertiy")
        actionPro.triggered.connect(self.proSignal.emit)
        menu.addActions([actionPro, Action(FIF.CANCEL, "Undo")])

        # show menu
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def createDir(self, name: str):
        card = Card(IndexType.DIR, name, self.scrolWidget)
        card.doubleClickSignal.connect(self.inDirSignal.emit)
        card.changeNameSignal.connect(self.changeNameSignal.emit)
        card.delSignal.connect(self.delSignal.emit)
        card.menuSignal.connect(self.menuSignal.emit)
        card.copySignal.connect(self.copySignal.emit)
        self.flowLayout.addWidget(card)

    def createFile(self, name: str):
        card = Card(IndexType.FILE, name, self.scrolWidget)
        card.doubleClickSignal.connect(self.openFileSignal.emit)
        card.menuSignal.connect(self.menuSignal.emit)
        card.delSignal.connect(self.delSignal.emit)
        card.changeNameSignal.connect(self.changeNameSignal.emit)
        card.copySignal.connect(self.copySignal.emit)

        self.flowLayout.addWidget(card)

    def reset(self, root: MyNode):
        item_list = list(range(self.flowLayout.count()))
        item_list.reverse()
        for i in item_list:
            item = self.flowLayout.takeAt(i)
            if item:
                item.deleteLater()
        for child in root.children:
            if child.index.type == IndexType.DIR:
                self.createDir(child.name)
            elif child.index.type == IndexType.FILE:
                self.createFile(child.name)


class Interface(QFrame):
    """
    单个界面
    """

    dirSignal = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hLayout = QHBoxLayout()

        self.line = QFrame(self)
        self.line.setFixedSize(1, MAINWINDOW_SIZE[1] // 2)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.copyInfo: MyNode = None

        # 应该是要在这里把东西全部读出来然后按照读的东西创建界面，然后操作的话就是发出信号\
        self.memCon = MemController(Config())

        self.slider = Slider(self.memCon.getModel(), self)
        self.nowNode = self.memCon.getRoot()
        self.view = View(self.nowNode, self)

        self._initConnections()
        self._initQss()
        self._initLayout()

    def _initLayout(self):
        self.setLayout(self.hLayout)

        self.hLayout.addWidget(self.slider)
        self.hLayout.addWidget(self.line, 0, Qt.AlignmentFlag.AlignVCenter)
        self.hLayout.addWidget(self.view)

    def _initConnections(self):
        self.view.addDirSignal.connect(self.createDir)
        self.view.inDirSignal.connect(self.inDir)
        self.view.openFileSignal.connect(self.openFile)
        self.view.addFileSignal.connect(self.createFile)
        self.view.menuSignal.connect(self.createMenu)
        self.view.delSignal.connect(self.delete)
        self.view.changeNameSignal.connect(self.changeName)
        self.view.proSignal.connect(self.showBitView)
        self.view.copySignal.connect(self.copy)
        self.view.pasteSignal.connect(self.paste)

        self.slider.homeSignal.connect(self.home)
        self.slider.backSignal.connect(self.back)
        self.slider.resetSignal.connect(self.reset)
        self.slider.changeSignal.connect(self.changeNode)

        self.memCon.noEnoughSignal.connect(self.noEnough)

    def noEnough(self):
        title = "⚠警告⚠"
        content = """磁盘空间不足，无法进行操作"""
        w = MessageBox(title, content, self)
        w.exec()

    def changeNode(self, node: MyNode):
        self.nowNode = node
        path = myGetPath(self.nowNode)
        self.dirSignal.emit(path)
        self.view.reset(self.nowNode)

    def copy(self, name: str):
        if self.nowNode.getChildByName(name):
            node = self.nowNode.getChildByName(name)
            self.copyInfo = copy.deepcopy(node)

    def paste(self):
        if self.copyInfo:
            # 还要检查名字
            self.copyInfo.changeName(
                self.memCon.chackName(self.nowNode, self.copyInfo.name)
            )
            if self.copyInfo.index.type == IndexType.FILE:
                self.nowNode.appendChild(self.copyInfo)
                if self.copyInfo.index.blockNo:
                    self.memCon.copyFile(self.copyInfo)
            elif self.copyInfo.index.type == IndexType.DIR:
                self._paste(self.nowNode, self.copyInfo)
            self.slider.updateModel()
            self.view.reset(self.nowNode)

    def _paste(self, faNode: MyNode, node: MyNode):
        if node.index.type == IndexType.DIR:
            # 这边因为加了新节点children会变，所以先复制一遍让它不会变,然后把它的孩子都删了
            children = copy.deepcopy(node.children)
            node.children = []
            for child in children:
                self._paste(node, child)
        elif node.index.type == IndexType.FILE:
            if node.index.blockNo:
                self.memCon.copyFile(node)
        faNode.appendChild(node)

    def showBitView(self):
        content = self.memCon.getBitMap()
        # 将列表转换为字符串，并在每组之间添加换行符
        content = "\n".join(content)
        w = MessageBox("位视图", content, self)
        w.exec()

    def home(self):
        self.nowNode = self.memCon.getRoot()
        path = myGetPath(self.nowNode)
        self.dirSignal.emit(path)
        self.view.reset(self.nowNode)

    def back(self):
        if self.nowNode.parent:
            self.nowNode = self.nowNode.parent
        path = myGetPath(self.nowNode)
        self.dirSignal.emit(path)
        self.view.reset(self.nowNode)

    def reset(self):
        title = "⚠警告⚠"
        content = """格式化后将会清空所有数据，是否继续？"""
        w = MessageBox(title, content, self)
        w.yesSignal.connect(self._reset)
        w.exec()

    def _reset(self):
        self.memCon.reset()
        self.nowNode = self.memCon.getRoot()
        self.view.reset(self.nowNode)
        self.slider.reset(self.memCon.getModel())

    def changeName(self, name: str, card: QFrame):
        if self.nowNode.getChildByName(name):
            node = self.nowNode.getChildByName(name)
            newName = MyMessageBox("请输入新的名字", "", self)
            newName.exec()
            newNew = newName.contentLabel.toPlainText()
            if newNew:
                node.index.name = newNew
                node.name = newNew
                self.slider.updateModel()
                card.name_label.setText(newNew)
                card.name_label.setToolTip(newNew)

    def delete(self, name: str):
        if self.nowNode.getChildByName(name):
            node = self.nowNode.getChildByName(name)
            self.memCon.deleteNode(self.nowNode, node)
            # 这边要及时更新，我感觉他是会定时检查的，是在主线程里的？所以不及时更新他会崩溃
            self.slider.updateModel()

    def createMenu(self, name: str):
        if self.nowNode.getChildByName(name):
            index: Index = self.nowNode.getChildByName(name).index
            node = self.nowNode.getChildByName(name)
            if index.type == IndexType.DIR:
                title = name
                count_dir = 0
                count_file = 0
                # 遍历子节点，并统计不同类型的子节点的数量
                for child in node.children:
                    if child.index.type == IndexType.DIR:
                        count_dir += 1
                    elif child.index.type == IndexType.FILE:
                        count_file += 1
                content = f"""类型：{index.type.name}\n包含{count_dir}个文件夹\n包含{count_file}个文件\n   """
                w = MessageBox(title, content, self)
                w.exec()
            elif index.type == IndexType.FILE:
                title = name
                content = f"""类型：{index.type.name}\n大小：{index.size}字节\n最后编辑时间：{index.modifyTime}\n首块号：{index.blockNo}   """
                w = MessageBox(title, content, self)
                w.exec()

    def openFile(self, name: str):
        if self.nowNode.getChildByName(name):
            fileIndex = self.nowNode.getChildByName(name).index
            content = None
            if fileIndex.blockNo == None:
                content = ""
            else:
                content = self.memCon.readFile(fileIndex)
            file = File(fileIndex.name, content, self)
            file.saveSignal.connect(self.saveFile)
            file.exec()

    def saveFile(self, name, content, time):
        index = self.nowNode.getChildByName(name).index
        self.memCon.writeFile(index, content, time)

    def createDir(self):
        name = self.memCon.addIndex(self.nowNode, None, IndexType.DIR)
        if name:
            self.slider.updateModel()
            self.view.createDir(name)

    def createFile(self):
        name = self.memCon.addIndex(self.nowNode, None, IndexType.FILE)
        if name:
            self.slider.updateModel()
            self.view.createFile(name)

    def inDir(self, name: str):
        if self.nowNode.getChildByName(name):
            self.nowNode = self.nowNode.getChildByName(name)
            path = myGetPath(self.nowNode)
            self.dirSignal.emit(path)
            self.view.reset(self.nowNode)

    def _initQss(self):
        self.setStyleSheet(
            f"Interface{{background: rgba{NORMAL_COLOR_RGBA2}; border-radius: {RADIUS}px;}}"
        )

    def saveAll(self):
        self.memCon.saveAll()


class MainWindow(QWidget):
    """
    程序的主界面
    """

    def __init__(self):
        super().__init__()
        self.resize(MAINWINDOW_SIZE[0], MAINWINDOW_SIZE[1])

        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.demo = Interface(self)
        self.demo.dirSignal.connect(lambda path: self.pivot.items["demo"].setText(path))

        self.addSubInterface(self.demo, "demo", "📄：.  （当前路径）")

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.demo)
        self.pivot.setCurrentItem(self.demo.objectName())

        self._initQss()
        self._initLayout()

    def _initLayout(self):
        self.setLayout(self.vBoxLayout)

        self.vBoxLayout.addWidget(self.pivot)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)

    def _initQss(self):
        self.setStyleSheet(f"MainWindow{{background: {BACK_COLOR}}}")

    def addSubInterface(self, widget: QWidget, objectName, text):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

    def closeEvent(self, e):
        self.demo.saveAll()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.setWindowTitle("同济软院2023春OS课设文件管理系统_2151641_王佳垚")
    w.show()
    app.exec()
