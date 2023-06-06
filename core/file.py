from .index import *
import datetime


class File:
    """
    文件本体
    """

    def __init__(self, name: str, content: str = ""):
        self.name = name
        self.content = content
        self.startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.endtime = None

    def save(self, content: str):
        self.content = content
        self.endtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def getName(self):
        return self.name

    def getContent(self):
        return self.content
