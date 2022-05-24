import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QApplication, QTabWidget, QGraphicsScene, QFileDialog, QMessageBox

from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Slot, Qt, QDir
from PySide6.QtGui import QPixmap, QIcon, QImageReader, QGuiApplication

class MyApplication():
    def __init__(self):
        loader = QUiLoader()
        self.window = loader.load("mainwindow.ui", None)
        self.mainwindow_setup(self.window)
        self.window.show()

    def mainwindow_setup(self, w):
        w.setWindowTitle("Image Processing")
        w.resize(1000,800)

        app_icon = QIcon()
        app_icon.addFile('star_white.png')
        w.setWindowIcon(app_icon)

        w.load_button.clicked.connect(lambda l: self.load_button_event())
        w.save_button.clicked.connect(lambda l: self.save_button_event())
        w.reset_button.clicked.connect(lambda l: self.reset_button_event())
        w.undo_button.clicked.connect(lambda l: self.undo_button_event())

        w.treeWidget.itemClicked.connect(self.item_clicked_event)
        w.treeWidget.expandAll()

        pixmap = QPixmap("star_white.png")
        w.icon_label.setScaledContents(True)
        w.icon_label.setPixmap(pixmap)

    @Slot()
    def load_button_event(self):
        self.image_file_name = QFileDialog.getOpenFileName(self.window, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")
        reader = QImageReader(self.image_file_name[0])
        reader.setAutoTransform(True)
        new_image = reader.read()
        if (new_image.isNull()):
            print("Image not found")

        self.scene = QGraphicsScene()
        pixmap = QPixmap.fromImage(new_image)

        self.scene.addPixmap(pixmap)
        self.window.graphicsView.setScene(self.scene)
        item = self.window.graphicsView.items()
        self.window.graphicsView.fitInView(item[0],Qt.KeepAspectRatio)
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
            self.window.tabWidget.setCurrentIndex(1)
        elif item_name == "Swirl Effect":
            self.window.tabWidget.setCurrentIndex(2)
        elif item_name == "Waves Effect":
            self.window.tabWidget.setCurrentIndex(3)
        elif item_name == "Cylinder Anamorphosis":
            self.window.tabWidget.setCurrentIndex(4)
        elif item_name == "Radial Blur Effect":
            self.window.tabWidget.setCurrentIndex(5)
        elif item_name == "Perspective Mapping":
            self.window.tabWidget.setCurrentIndex(6)
        elif item_name == "Custom Effect":
            self.window.tabWidget.setCurrentIndex(7)
        elif item_name == "Median Blurring":
            self.window.tabWidget.setCurrentIndex(8)
        elif item_name == "Gaussian Filtering":
            self.window.tabWidget.setCurrentIndex(9)
        elif item_name == "Bilateral Filter":
            self.window.tabWidget.setCurrentIndex(10)
        elif item_name == "About":
            self.window.tabWidget.setCurrentIndex(0)

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    ma = MyApplication()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    app.exec()