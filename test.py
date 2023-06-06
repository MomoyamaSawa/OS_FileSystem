from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import *
from setting import *
from qfluentwidgets import FluentIcon as FIF


# 创建主窗口并设置垂直布局
mainWindow = QMainWindow()
vLayout = QVBoxLayout(mainWindow.centralWidget())
mainWindow.centralWidget().setLayout(vLayout)

# 创建一个 QWidget 作为容器，并将其设置为水平布局
container = QWidget()
hLayout = QHBoxLayout(container)
container.setLayout(hLayout)

# 添加子部件到水平布局中
childWidget1 = QLabel("Hello")
childWidget2 = QPushButton("World")
hLayout.addWidget(childWidget1)
hLayout.addWidget(childWidget2)

# 将容器添加到主窗口的垂直布局中
vLayout.addWidget(container)

# 将容器的大小策略设置为 QSizePolicy::Preferred
container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

# 重新计算容器的最佳大小
container.adjustSize()
