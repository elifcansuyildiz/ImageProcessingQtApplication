import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QTabWidget

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot

class MyApplication():
    def __init__(self):
        loader = QUiLoader()
        self.window = loader.load("mainwindow.ui", None)
        self.mainwindow_setup(self.window)
        self.window.show()

    def mainwindow_setup(self, w):
        w.setWindowTitle("Image Processing")

        w.load_button.clicked.connect(lambda l: self.load_button_event())
        w.save_button.clicked.connect(lambda l: self.save_button_event())
        w.reset_button.clicked.connect(lambda l: self.reset_button_event())
        w.undo_button.clicked.connect(lambda l: self.undo_button_event())

        w.treeWidget.itemClicked.connect(self.item_clicked_event)
        #w.treeWidget.expandAll()

    @Slot()
    def load_button_event(self):
        print("loaded")

    @Slot()
    def save_button_event(self):
        print("saved")

    @Slot()
    def reset_button_event(self):
        print("reseted")

    @Slot()
    def undo_button_event(self):
        print("undone")

    @Slot()
    def item_clicked_event(self, position, column):
        # get item name from the tree on the left bar
        item_name = position.text(column)
        print(item_name)
        if item_name == "Fish Eye Effect":
            self.window.tabWidget.setCurrentIndex(0)
        elif item_name == "Swirl Effect":
            self.window.tabWidget.setCurrentIndex(1)
        elif item_name == "Waves Effect":
            self.window.tabWidget.setCurrentIndex(2)
        elif item_name == "Cylinder Anamorphosis":
            self.window.tabWidget.setCurrentIndex(3)
        elif item_name == "Radial Blur Effect":
            self.window.tabWidget.setCurrentIndex(4)
        elif item_name == "Perspective Mapping":
            self.window.tabWidget.setCurrentIndex(5)
        elif item_name == "Custom Effect":
            self.window.tabWidget.setCurrentIndex(6)

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    ma = MyApplication()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()