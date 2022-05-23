import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QTabWidget

from PySide6.QtUiTools import QUiLoader

class MyApplication():
    def __init__(self):
        loader = QUiLoader()
        self.window = loader.load("mainwindow.ui", None)
        self.mainwindow_setup(self.window)
        self.window.show()

    def mainwindow_setup(self, w):
        w.setWindowTitle("Image Processing")

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    ma = MyApplication()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()