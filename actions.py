from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

__author__ = "Atinderpal Singh"
__license__ = "MIT"
__version__ = "1.0"
__email__ = "atinderpalap@gmail.com"


# subclass
class CheckableComboBox(QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    def addItem(self, item):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count()-1,0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Checked)

    def itemChecked(self, index):
        item = self.model().item(i,0)
        return item.checkState() == QtCore.Qt.Checked

class ImageViewer:
    ''' Basic image viewer class to show an image with zoom and pan functionaities.
        Requirement: Qt's Qlabel widget name where the image will be drawn/displayed.
    '''
    def __init__(self, qlabel, parent = None):
        self.qlabel_image = qlabel                            # widget/window name where image is displayed (I'm usiing qlabel)
        self.parent = parent
        self.qimage_scaled = QImage()                         # scaled image to fit to the size of qlabel_image
        self.qpixmap = QPixmap()                              # qpixmap to fill the qlabel_image

        self.zoomX = 1              # zoom factor w.r.t size of qlabel_image
        self.position = [0, 0]      # position of top left corner of qimage_label w.r.t. qimage_scaled
        self.panFlag = False        # to enable or disable pan

        self.qlabel_image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.__connectEvents()

    def __connectEvents(self):
        # Mouse events
        self.qlabel_image.mousePressEvent = self.mousePressAction
        self.qlabel_image.mouseMoveEvent = self.mouseMoveAction
        self.qlabel_image.mouseReleaseEvent = self.mouseReleaseAction

    def onResize(self):
        ''' things to do when qlabel_image is resized '''
        self.qpixmap = QPixmap(self.qlabel_image.size())
        self.qpixmap.fill(QtCore.Qt.gray)
        self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
        self.update(self.instance)

    def loadImage(self, imagePath, instance=None):
        ''' To load and display new image.'''
        self.qimage = QImage(imagePath)
        if instance is not None:
            penRectangle = QPen(Qt.green)
            penRectangle.setWidth(20)

            painterInstance = QPainter(self.qimage)
            img_height = self.qlabel_image.height()

            self.parent.qlist_objects.clear()
            for i in range(len(instance)):
                object_dict = instance[i]

                for object_type in object_dict:
                    # print("Type : " + object_type)
                    hlayout = QHBoxLayout()
                    obj_type_label = QLabel()
                    obj_type_label.setText(object_type)
                    hlayout.addWidget(obj_type_label)
                    attrib = object_dict[object_type]
                    comboBox = CheckableComboBox(self.parent)

                    for j in range(len(attrib)):
                        params = attrib[j]
                        bbox = params["bbox"]
                        painterInstance.setPen(penRectangle)
                        painterInstance.drawRect(bbox[0], bbox[1], bbox[2], bbox[3])

                        penText = QPen(Qt.red)
                        penText.setWidth(10)
                        painterInstance.setPen(penText)
                        painterInstance.setFont(QFont('Decorative', 0.05 * img_height))
                        painterInstance.drawText(bbox[0], max(bbox[1] - 20, 20), params["id"])
                        comboBox.addItem(params["id"])

                    hlayout.addWidget(comboBox)
                    del_button = QPushButton('Delete')
                    add_button = QPushButton('Add')
                    hlayout.addWidget(add_button)
                    hlayout.addWidget(del_button)

                hlayout.addStretch()

                hlayout.setSizeConstraint(QLayout.SetFixedSize)

                widget = QWidget()
                widget.setLayout(hlayout)
                itemN = QListWidgetItem()
                itemN.setSizeHint(widget.sizeHint())
                self.parent.qlist_objects.addItem(itemN)
                self.parent.qlist_objects.setItemWidget(itemN, widget)
            painterInstance.end()

        self.qpixmap = QPixmap(self.qlabel_image.size())
        self.instance = instance
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width(), self.qlabel_image.height(), QtCore.Qt.KeepAspectRatio)
            self.update(instance)
        else:
            self.statusbar.showMessage('Cannot open this image! Try another one.', 5000)

    def update(self, instance=None):
        ''' This function actually draws the scaled image to the qlabel_image.
            It will be repeatedly called when zooming or panning.
            So, I tried to include only the necessary operations required just for these tasks. 
        '''
        if not self.qimage_scaled.isNull():
            # check if position is within limits to prevent unbounded panning.
            px, py = self.position
            px = px if (px <= self.qimage_scaled.width() - self.qlabel_image.width()) else (self.qimage_scaled.width() - self.qlabel_image.width())
            py = py if (py <= self.qimage_scaled.height() - self.qlabel_image.height()) else (self.qimage_scaled.height() - self.qlabel_image.height())
            px = px if (px >= 0) else 0
            py = py if (py >= 0) else 0
            self.position = (px, py)

            if self.zoomX == 1:
                self.qpixmap.fill(QtCore.Qt.white)

            # the act of painting the qpixamp
            painter = QPainter()
            painter.begin(self.qpixmap)
            painter.drawImage(QtCore.QPoint(0, 0), self.qimage_scaled,
                    QtCore.QRect(self.position[0], self.position[1], self.qlabel_image.width(), self.qlabel_image.height()) )
            painter.end()
            self.qlabel_image.setPixmap(self.qpixmap)
        else:
            pass

    def mousePressAction(self, QMouseEvent):
        x, y = QMouseEvent.pos().x(), QMouseEvent.pos().y()
        if self.panFlag:
            self.pressed = QMouseEvent.pos()    # starting point of drag vector
            self.anchor = self.position         # save the pan position when panning starts

    def mouseMoveAction(self, QMouseEvent):
        x, y = QMouseEvent.pos().x(), QMouseEvent.pos().y()
        if self.pressed:
            dx, dy = x - self.pressed.x(), y - self.pressed.y()         # calculate the drag vector
            self.position = self.anchor[0] - dx, self.anchor[1] - dy    # update pan position using drag vector
            self.update(self.instance)                                               # show the image with udated pan position

    def mouseReleaseAction(self, QMouseEvent):
        self.pressed = None                                             # clear the starting point of drag vector

    def zoomPlus(self):
        self.zoomX += 1
        px, py = self.position
        px += self.qlabel_image.width()/2
        py += self.qlabel_image.height()/2
        self.position = (px, py)
        self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
        self.update(self.instance)

    def zoomMinus(self):
        if self.zoomX > 1:
            self.zoomX -= 1
            px, py = self.position
            px -= self.qlabel_image.width()/2
            py -= self.qlabel_image.height()/2
            self.position = (px, py)
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
            self.update(self.instance)

    def resetZoom(self):
        self.zoomX = 1
        self.position = [0, 0]
        self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
        self.update(self.instance)

    def enablePan(self, value):
        self.panFlag = value