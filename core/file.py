from .index import *
import datetime
from qfluentwidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from tool import *


class File(MyMessageBox):
    """
    文件本体
    """

    saveSignal = pyqtSignal(str, str, str)

    def __init__(self, name: str, content: str = "", parent=None):
        super().__init__(name, content, parent)
        self.name = name
        self.startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.endtime = None

        self.yesButton.clicked.connect(self.save)

    def save(self, content: str):
        self.content = self.contentLabel.toPlainText()
        self.endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.saveSignal.emit(self.name, self.content, self.endtime)

    def getName(self):
        return self.name

    def getContent(self):
        return self.content
