from qfluentwidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from setting import *
from core.index import *


class MaskDialogBase(QDialog):
    """Dialog box base class with a mask"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._hBoxLayout = QHBoxLayout(self)
        self.windowMask = QWidget(self)

        # dialog box in the center of mask, all widgets take it as parent
        self.widget = QFrame(self, objectName="centerWidget")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, parent.width(), parent.height())

        c = 0 if isDarkTheme() else 255
        self.windowMask.resize(self.size())
        self.windowMask.setStyleSheet(f"background:rgba({c}, {c}, {c}, 0.6)")
        self._hBoxLayout.addWidget(self.widget)
        self.setShadowEffect()

        self.window().installEventFilter(self)

    def setShadowEffect(
        self, blurRadius=60, offset=(0, 10), color=QColor(0, 0, 0, 100)
    ):
        """add shadow to dialog"""
        shadowEffect = QGraphicsDropShadowEffect(self.widget)
        shadowEffect.setBlurRadius(blurRadius)
        shadowEffect.setOffset(*offset)
        shadowEffect.setColor(color)
        self.widget.setGraphicsEffect(None)
        self.widget.setGraphicsEffect(shadowEffect)

    def setMaskColor(self, color: QColor):
        """set the color of mask"""
        self.windowMask.setStyleSheet(
            f"""
            background: rgba({color.red()}, {color.blue()}, {color.green()}, {color.alpha()})
        """
        )

    def showEvent(self, e):
        """fade in"""
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        opacityAni = QPropertyAnimation(opacityEffect, b"opacity", self)
        opacityAni.setStartValue(0)
        opacityAni.setEndValue(1)
        opacityAni.setDuration(200)
        opacityAni.setEasingCurve(QEasingCurve.Type.InSine)
        opacityAni.finished.connect(opacityEffect.deleteLater)
        opacityAni.start()
        super().showEvent(e)

    def closeEvent(self, e):
        """fade out"""
        self.widget.setGraphicsEffect(None)
        opacityEffect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(opacityEffect)
        opacityAni = QPropertyAnimation(opacityEffect, b"opacity", self)
        opacityAni.setStartValue(1)
        opacityAni.setEndValue(0)
        opacityAni.setDuration(100)
        opacityAni.setEasingCurve(QEasingCurve.Type.OutCubic)
        opacityAni.finished.connect(self.deleteLater)
        opacityAni.start()
        e.ignore()

    def resizeEvent(self, e):
        self.windowMask.resize(self.size())

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Type.Resize:
                self.resize(e.size())

        return super().eventFilter(obj, e)


class Ui_MessageBox:
    """Ui of message box"""

    yesSignal = pyqtSignal()
    cancelSignal = pyqtSignal()

    def _setUpUi(self, title, content, parent):
        self.content = content
        self.titleLabel = QLabel(title, parent)
        self.contentLabel = TextEdit(parent)
        self.contentLabel.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        self.contentLabel.setAcceptRichText(True)
        self.contentLabel.setPlainText(content)
        self.contentLabel.setFixedSize(FILE_SIZE[0], FILE_SIZE[1])

        self.buttonGroup = QFrame(parent)
        self.yesButton = PrimaryPushButton(self.tr("OK"), self.buttonGroup)
        self.cancelButton = QPushButton(self.tr("Cancel"), self.buttonGroup)

        self.vBoxLayout = QVBoxLayout(parent)
        self.textLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout(self.buttonGroup)

        self.__initWidget()

    def __initWidget(self):
        self.__setQss()
        self.__initLayout()

        # fixes https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/19
        self.yesButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)
        self.cancelButton.setAttribute(Qt.WidgetAttribute.WA_LayoutUsesWidgetRect)

        self.yesButton.setFocus()
        self.buttonGroup.setFixedHeight(81)

        # self._adjustText()

        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    def _adjustText(self):
        if self.isWindow():
            if self.parent():
                w = max(self.titleLabel.width(), self.parent().width())
                chars = max(min(w / 9, 140), 30)
            else:
                chars = 100
        else:
            w = max(self.titleLabel.width(), self.window().width())
            chars = max(min(w / 9, 100), 30)

        self.contentLabel.setText(TextWrap.wrap(self.content, chars, True)[0])

    def __initLayout(self):
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.textLayout, 1)
        self.vBoxLayout.addWidget(self.buttonGroup, 0, Qt.AlignmentFlag.AlignBottom)
        self.vBoxLayout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)

        self.textLayout.setSpacing(12)
        self.textLayout.setContentsMargins(24, 24, 24, 24)
        self.textLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignTop)
        self.textLayout.addWidget(self.contentLabel, 0, Qt.AlignmentFlag.AlignTop)

        self.buttonLayout.setSpacing(12)
        self.buttonLayout.setContentsMargins(24, 24, 24, 24)
        self.buttonLayout.addWidget(self.yesButton, 1, Qt.AlignmentFlag.AlignVCenter)
        self.buttonLayout.addWidget(self.cancelButton, 1, Qt.AlignmentFlag.AlignVCenter)

    def __onCancelButtonClicked(self):
        self.reject()
        self.cancelSignal.emit()

    def __onYesButtonClicked(self):
        self.accept()
        self.yesSignal.emit()

    def __setQss(self):
        self.titleLabel.setObjectName("titleLabel")
        self.contentLabel.setObjectName("contentLabel")
        self.buttonGroup.setObjectName("buttonGroup")
        self.cancelButton.setObjectName("cancelButton")

        FluentStyleSheet.DIALOG.apply(self)

        self.yesButton.adjustSize()
        self.cancelButton.adjustSize()


class MyMessageBox(MaskDialogBase, Ui_MessageBox):
    """Message box"""

    yesSignal = pyqtSignal()
    cancelSignal = pyqtSignal()

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent=parent)
        self._setUpUi(title, content, self.widget)

        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        self._hBoxLayout.removeWidget(self.widget)
        self._hBoxLayout.addWidget(self.widget, 1, Qt.AlignmentFlag.AlignCenter)

        self.buttonGroup.setMinimumWidth(280)
        self.widget.setFixedSize(
            max(self.contentLabel.width(), self.titleLabel.width()) + 48,
            self.contentLabel.y() + self.contentLabel.height() + 105,
        )

    def eventFilter(self, obj, e: QEvent):
        if obj is self.window():
            if e.type() == QEvent.Type.Resize:
                self._adjustText()

        return super().eventFilter(obj, e)


class RoundWidget(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(
            NORMAL_COLOR_RGBA1_[0],
            NORMAL_COLOR_RGBA1_[1],
            NORMAL_COLOR_RGBA1_[2],
            NORMAL_COLOR_RGBA1_[3],
        )
        color.setAlpha(64)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)


def myGetPath(node: MyNode):
    return "📄：" + node.getPath() + "  （当前路径）"
