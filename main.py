#!/usr/bin/env python

''' A basic GUi to use ImageViewer class to show its functionalities and use cases. '''

from PyQt5 import *
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from actions import ImageViewer
import sys, os
import json

gui = uic.loadUiType("main.ui")[0]     # load UI file designed in Qt Designer
VALID_FORMAT = ('.BMP', '.GIF', '.JPG', '.JPEG', '.PNG', '.PBM', '.PGM', '.PPM', '.TIFF', '.XBM')  # Image formats supported by Qt

class Iwindow(QtWidgets.QMainWindow, gui):
    def __init__(self, json_file, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.json_file = json_file
        self.json_data = self.get_json_data(self.json_file)
        self.setupUi(self)

        self.cntr, self.numImages = -1, -1  # self.cntr have the info of which image is selected/displayed

        self.image_viewer = ImageViewer(self.qlabel_image, self)
        self.__connectEvents()
        self.showMaximized()
        self.selectDir(False)

    def get_json_data(self, path):
        print('json path ' + str(path))
        cwd = os.getcwd()
        file_path = cwd + '/' + path
        with open(file_path, 'r+') as json_file:
            return json.load(json_file)

    def getImages(self, folder):
        ''' Get the names and paths of all the images in a directory. '''
        image_list = []

        if folder is None:
            if self.json_data is not None:
                img_arr = self.json_data["samples"]
                for i in range(len(img_arr)):
                    image_obj = {'name': str(img_arr[i]["id"]), 'path': img_arr[i]["img_path"]}
                    image_list.append(image_obj)
            return image_list

        if os.path.isdir(folder):
            for file in os.listdir(folder):
                if file.upper().endswith(VALID_FORMAT):
                    im_path = os.path.join(folder, file)
                    image_obj = {'name': file, 'path': im_path}
                    image_list.append(image_obj)


        return image_list

    def __connectEvents(self):
        self.open_folder.clicked.connect(self.selectDir)
        self.next_im.clicked.connect(self.nextImg)
        self.prev_im.clicked.connect(self.prevImg)
        self.save_im.clicked.connect(self.image_viewer.saveJson)
        self.qlist_images.itemClicked.connect(self.item_click)
        # self.save_im.clicked.connect(self.saveImg)

        prev_im_shortcut = QShortcut(QKeySequence.MoveToPreviousChar, self)
        prev_im_shortcut.activated.connect(self.prevImg)

        next_im_shortcut = QShortcut(QKeySequence.MoveToNextChar, self)
        next_im_shortcut.activated.connect(self.nextImg)

        self.zoom_plus.clicked.connect(self.image_viewer.zoomPlus)
        self.zoom_minus.clicked.connect(self.image_viewer.zoomMinus)
        self.reset_zoom.clicked.connect(self.image_viewer.resetZoom)

        self.toggle_line.toggled.connect(self.action_line)
        self.toggle_rect.toggled.connect(self.action_rect)
        self.toggle_move.toggled.connect(self.action_move)

    def selectDir(self, load_folder=True):
        ''' Select a directory, make list of images in it and display the first image in the list. '''
        # open 'select folder' dialog box
        if load_folder is True:
            self.folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
            if not self.folder:
                QMessageBox.warning(self, 'No Folder Selected', 'Please select a valid Folder')
                return
        else:
            self.folder = None

        self.logs= self.getImages(self.folder)
        self.numImages = len(self.logs)

        # make qitems of the image names
        self.items = [QListWidgetItem(log['name']) for log in self.logs]
        for item in self.items:
            self.qlist_images.addItem(item)

        # display first image and enable Pan 
        self.cntr = 0
        self.image_viewer.enablePan(True)
        self.image_viewer.loadImage(self.logs[self.cntr]['path'])
        self.items[self.cntr].setSelected(True)

        # enable the next image button on the gui if multiple images are loaded
        if self.numImages > 1:
            self.next_im.setEnabled(True)

    def resizeEvent(self, evt):
        if self.cntr >= 0:
            self.image_viewer.onResize()

    def nextImg(self):
        if self.cntr < self.numImages -1:
            #self.image_viewer.saveJson()
            self.cntr += 1
            self.image_viewer.loadImage(self.logs[self.cntr]['path'])
            #self.qlist_images.setItemSelected(self.items[self.cntr], True)
            self.items[self.cntr].setSelected(True)
            self.qlist_images.scrollToItem(self.items[self.cntr], QAbstractItemView.PositionAtTop)
            #self.statusbar.showMessage('Path : ' + self.json_data['samples'][self.cntr]['img_path'])

        else:
            QMessageBox.warning(self, 'Sorry', 'No more Images!')

    def prevImg(self):
        if self.cntr > 0:
            #self.image_viewer.saveJson()
            self.cntr -= 1
            self.image_viewer.loadImage(self.logs[self.cntr]['path'])
            #self.qlist_images.setItemSelected(self.items[self.cntr], True)
            self.items[self.cntr].setSelected(True)
            self.qlist_images.scrollToItem(self.items[self.cntr], QAbstractItemView.PositionAtTop)
            #self.statusbar.showMessage('Path : ' + self.json_data['samples'][self.cntr]['img_path'])

        else:
            QMessageBox.warning(self, 'Sorry', 'No previous Image!')

    def item_click(self, item):
        self.cntr = self.items.index(item)
        self.image_viewer.loadImage(self.logs[self.cntr]['path'])

    def action_line(self):
        if self.toggle_line.isChecked():
            self.qlabel_image.setCursor(QtCore.Qt.CrossCursor)
            self.image_viewer.enablePan(False)

    def action_rect(self):
        if self.toggle_rect.isChecked():
            self.qlabel_image.setCursor(QtCore.Qt.CrossCursor)
            self.image_viewer.enablePan(False)

    def action_move(self):
        if self.toggle_move.isChecked():
            self.qlabel_image.setCursor(QtCore.Qt.OpenHandCursor)
            self.image_viewer.enablePan(True)

def main():
    if len(sys.argv) <= 1 :
        print("Please, supply the json file")
        sys.exit()
    json_file = str(sys.argv[1])
    app = QApplication([])
    app.setStyle(QStyleFactory.create("Cleanlooks"))
    app.setPalette(QApplication.style().standardPalette())
    parentWindow = Iwindow(json_file, None)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()