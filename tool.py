from qfluentwidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *


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


class MyMessageDialog(MaskDialogBase):
    yesSignal = pyqtSignal()
    cancelSignal = pyqtSignal()

    def __init__(self, title: str, content: str, parent):
        super().__init__(parent=parent)
        self.content = content
        self.titleLabel = QLabel(title, self.widget)
        self.contentLabel = TextEdit(self.widget)
        self.contentLabel.setMarkdown(content)
        self.yesButton = QPushButton(self.tr("OK"), self.widget)
        self.cancelButton = QPushButton(self.tr("Cancel"), self.widget)
        self.__initWidget()

    def __initWidget(self):
        """initialize widgets"""
        self.windowMask.resize(self.size())
        self.widget.setMaximumWidth(540)
        self.titleLabel.move(24, 24)
        self.contentLabel.move(24, 56)
        self.contentLabel.setText(TextWrap.wrap(self.content, 71)[0])

        self.__setQss()
        self.__initLayout()

        # connect signal to slot
        self.yesButton.clicked.connect(self.__onYesButtonClicked)
        self.cancelButton.clicked.connect(self.__onCancelButtonClicked)

    def __initLayout(self):
        """initialize layout"""
        self.contentLabel.adjustSize()
        self.widget.setFixedSize(
            48 + self.contentLabel.width(),
            self.contentLabel.y() + self.contentLabel.height() + 92,
        )
        self.yesButton.resize((self.widget.width() - 54) // 2, 32)
        self.cancelButton.resize(self.yesButton.width(), 32)
        self.yesButton.move(24, self.widget.height() - 56)
        self.cancelButton.move(
            self.widget.width() - 24 - self.cancelButton.width(),
            self.widget.height() - 56,
        )

    def __onCancelButtonClicked(self):
        self.cancelSignal.emit()
        self.reject()

    def __onYesButtonClicked(self):
        self.setEnabled(False)
        self.yesSignal.emit()
        self.accept()

    def __setQss(self):
        """set style sheet"""
        self.windowMask.setObjectName("windowMask")
        self.titleLabel.setObjectName("titleLabel")
        self.contentLabel.setObjectName("contentLabel")
        FluentStyleSheet.MESSAGE_DIALOG.apply(self)
