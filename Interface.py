from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import *
from setting import *
from qfluentwidgets import FluentIcon as FIF
from model import *


class Slider(QWidget):
    """
    侧边栏
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedWidth(SLIDER_WIDTH)

        self.vLayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()
        self.containner = QFrame(self)

        self.homeButton = ToolButton(FIF.HOME, self)
        self.backButton = ToolButton(FIF.CARE_LEFT_SOLID, self)
        self.forwardButton = ToolButton(FIF.CARE_RIGHT_SOLID, self)

        self.view = TreeView(self)
        model = FileSystemModel()
        self.view.setModel(model)

        self._initLayout()

    def _initLayout(self):
        self.setLayout(self.vLayout)
        self.containner.setLayout(self.hLayout)

        self.hLayout.addWidget(self.homeButton)
        self.hLayout.addWidget(self.backButton)
        self.hLayout.addWidget(self.forwardButton)

        self.vLayout.addWidget(self.containner)
        self.vLayout.addSpacing(20)
        self.vLayout.addWidget(self.view)

    def _initQss(self):
        pass


class Card(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置卡片的固定大小
        self.setFixedSize(CARD_SIZE[0], CARD_SIZE[1])

        # 文件图片
        self.icon_label = QLabel(self)
        pixmap = QPixmap(RESOURCE["file"])
        self.icon_label.setPixmap(pixmap.scaledToWidth(CARD_SIZE[1] // 2))

        # 文件名
        self.name_label = QLabel("test.txt", self)
        self.name_label.setStyleSheet(f"font-size: {FONT_SIZE}px")

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

    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)

        # add actions
        menu.addAction(Action(FIF.SEND_FILL, "Open"))

        # add actions
        menu.addActions(
            [
                Action(FIF.CUT, "Cut"),
                Action(FIF.COPY, "Copy"),
                Action(FIF.DELETE, "Delete"),
                Action(FIF.SETTING, "Propertiy"),
            ]
        )

        # show menu
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)


class View(QWidget):
    """
    视图
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vLayout = QVBoxLayout()

        self.searchBar = SearchLineEdit(self)
        self.searchBar.setPlaceholderText("请在此输入搜索内容")
        self.roundWidget = QWidget(self)
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

        card = Card(self.scrolWidget)
        self.flowLayout.addWidget(card)

        self._initQss()
        self._initLayout()

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
        self.scrolWidget.setStyleSheet("QWidget { background-color: transparent; }")

    def contextMenuEvent(self, e):
        menu = RoundMenu(parent=self)

        # add actions
        menu.addAction(Action(FIF.PASTE, "Paste"))

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
        submenu.addActions(
            [
                Action(FIF.VIDEO, "dir"),
                Action(FIF.MUSIC, "file"),
            ]
        )
        menu.addMenu(submenu)

        # add actions
        menu.addActions([Action(FIF.SETTING, "Propertiy"), Action(FIF.CANCEL, "Undo")])

        # show menu
        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)


class Interface(QFrame):
    """
    单个界面
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.hLayout = QHBoxLayout()

        self.line = QFrame(self)
        self.line.setFixedSize(1, MAINWINDOW_SIZE[1] // 2)
        self.line.setFrameShape(QFrame.Shape.VLine)

        self.slider = Slider(self)
        self.view = View(self)

        self._initQss()
        self._initLayout()

    def _initLayout(self):
        self.setLayout(self.hLayout)

        self.hLayout.addWidget(self.slider)
        self.hLayout.addWidget(self.line, 0, Qt.AlignmentFlag.AlignVCenter)
        self.hLayout.addWidget(self.view)

    def _initQss(self):
        # 注意这里覆盖了
        self.setStyleSheet(
            f"Interface{{background: rgba{NORMAL_COLOR_RGBA2}; border-radius: {RADIUS}px;}}"
        )


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
        # 添加分割线
        # self.line = QFrame(self)
        # self.line.setFixedSize(MAINWINDOW_SIZE[0] // 2, 1)
        # self.line.setFrameShape(QFrame.Shape.HLine)

        self.test1 = Interface(self)
        self.test2 = QFrame(self)
        self.test3 = QLabel("test3", self)

        self.addSubInterface(self.test1, "test1", "test1")
        self.addSubInterface(self.test2, "test2", "test2")
        self.addSubInterface(self.test3, "test3", "test3")

        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.test1)
        self.pivot.setCurrentItem(self.test1.objectName())

        self._initQss()
        self._initLayout()

    def _initLayout(self):
        self.setLayout(self.vBoxLayout)

        self.vBoxLayout.addWidget(self.pivot)
        # self.vBoxLayout.addWidget(self.line)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
