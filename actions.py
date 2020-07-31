'''
    Author : Ayush Dobhal
    Date created : 06/29/2020
    Description : Actions file
'''
from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, QPoint
import json

# subclass
class CheckableComboBox(QComboBox):
    def addItem(self, item, parent=None):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count() - 1, 0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Checked)

    def itemChecked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked

    def toggle(self, index):
        item = self.model().item(index, 0)
        if item.checkState()  == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)

class ImageViewer:
    ''' Basic image viewer class to show an image with zoom and pan functionaities.
        Requirement: Qt's Qlabel widget name where the image will be drawn/displayed.
    '''
    def __init__(self, qlabel, parent = None):
        self.qlabel_image = qlabel                            # widget/window name where image is displayed (I'm usiing qlabel)
        self.parent = parent
        self.image_path = ''
        self.qimage_scaled = QImage()                         # scaled image to fit to the size of qlabel_image
        self.qpixmap = QPixmap()                              # qpixmap to fill the qlabel_image

        self.zoomX = 1              # zoom factor w.r.t size of qlabel_image
        self.position = [0, 0]      # position of top left corner of qimage_label w.r.t. qimage_scaled
        self.panFlag = False        # to enable or disable pan
        self.current_instances = -1
        self.conf = self.parent.json_data['samples'][self.parent.cntr]['img_conf']

        self.qlabel_image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.qlabel_image.autoFillBackground()
        self.__connectEvents()

    def __connectEvents(self):
        # Mouse events
        self.qlabel_image.mousePressEvent = self.mousePressAction
        self.qlabel_image.mouseMoveEvent = self.mouseMoveAction
        self.qlabel_image.mouseReleaseEvent = self.mouseReleaseAction
        self.parent.remove_object.clicked.connect(self.removeSel)
        self.parent.add_object.clicked.connect(self.addObject)
        self.parent.save_json.clicked.connect(self.saveJson)

    def saveJson(self):
        #remaining_instances = []
        for index in range(self.parent.qlist_objects.count()):
            item = self.parent.qlist_objects.item(index)
            widget = self.parent.qlist_objects.itemWidget(item)
            #curr_obj_dict = {}
            label_widget = None
            combobox_widget = None
            qline_widget = None
            for ch in widget.children():
                if (ch.__class__.__name__ == 'QLabel'):
                    label_widget = ch
                elif (ch.__class__.__name__ == 'CheckableComboBox'):
                    combobox_widget = ch
                else:
                    qline_widget = ch

            label_txt = label_widget.text()
            label_split = label_txt.split('.')
            object_idx = int(label_split[0])
            object_name = label_split[1]
            count = int(qline_widget.text())
            #curr_obj_dict = self.parent.json_data['samples'][self.parent.cntr][object_idx]
            self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx]['instance_count'] = count
            #remaining_instances.append(curr_obj_dict)

        if self.parent.check_status.checkState() == QtCore.Qt.Checked:
            self.parent.json_data['samples'][self.parent.cntr]['complete'] = True
        else:
            self.parent.json_data['samples'][self.parent.cntr]['complete'] = False

        #self.parent.json_data['samples'][self.parent.cntr]['instances'] = remaining_instances
        with open(self.parent.json_file, 'w') as outfile:
            json.dump(self.parent.json_data, outfile, indent=4)

    def onResize(self):
        ''' things to do when qlabel_image is resized '''
        self.qpixmap = QPixmap(self.qlabel_image.size())
        self.qpixmap.fill(QtCore.Qt.gray)
        self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
        self.update(self.instance)

    def createFilterArea(self, conf):
        instance = self.parent.json_data['samples'][self.parent.cntr]['instances']
        if self.current_instances == -1:
            self.current_instances = len(instance)

        if instance is not None:
            self.parent.qlist_objects.clear()
            for i in range(len(instance)):
                object_dict = instance[i]
                if self.parent.json_data['samples'][self.parent.cntr]['instances'][i]['selected'] is False:
                    continue

                object_dict = self.parent.json_data['samples'][self.parent.cntr]['instances'][i]
                if self.parent.json_data['samples'][self.parent.cntr]['complete'] is False:
                    self.parent.check_status.setChecked(False)
                else:
                    self.parent.check_status.setChecked(True)
                for object_type in object_dict:
                    if object_type == 'selected' or object_type == 'instance_count':
                        continue
                    hlayout = QHBoxLayout()
                    obj_type_label = QLabel()
                    obj_type_label.setText(str(i) + '.' + object_type)
                    hlayout.addWidget(obj_type_label)
                    comboBox = CheckableComboBox(self.parent)
                    comboBox.setStyleSheet('''*    
                            QComboBox QAbstractItemView 
                                {
                                min-width: 120px;
                                }
                            ''')
                    tbox = QLineEdit()
                    tbox.setText(str(self.parent.json_data['samples'][self.parent.cntr]['instances'][i]['instance_count']))
                    #hlayout.addWidget(comboBox)
                    hlayout.addWidget(tbox)
                    hlayout.addStretch()
                    hlayout.setSizeConstraint(QLayout.SetFixedSize)

                    widget = QWidget()
                    widget.setLayout(hlayout)
                    itemN = QListWidgetItem()
                    itemN.setSizeHint(widget.sizeHint())
                    self.parent.qlist_objects.addItem(itemN)
                    self.parent.qlist_objects.setItemWidget(itemN, widget)

    def drawBbox(self, imagePath, conf=None):
        ''' To load and display new image.'''
        instance = self.parent.json_data['samples'][self.parent.cntr]['instances']
        self.qimage = QImage(imagePath)
        self.qpixmap = QPixmap(self.qlabel_image.size())
        self.instance = instance
        if not self.qimage.isNull():
            # reset Zoom factor and Pan position
            self.zoomX = 1
            self.position = [0, 0]
            self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width(), self.qlabel_image.height(),
                                                    QtCore.Qt.KeepAspectRatio)
            self.update(instance)

    def loadImage(self, imagePath, conf=None):
        ''' To load and display new image.'''
        conf = self.parent.json_data['samples'][self.parent.cntr]['img_conf']
        self.createFilterArea(conf)
        self.drawBbox(imagePath, conf)

    def removeSel(self, cbox=None):
        #if cbox is not None:
        #    decision = cbox.isChecked()
        decision = False
        listItems = self.parent.qlist_objects.selectedItems()
        if not listItems:
            QMessageBox.warning(self.parent, 'No object selected', 'Please select some objects to remove')
            return

        for item in listItems:
            #selected = self.parent.qlist_objects.takeItem(self.parent.qlist_objects.row(item))
            widget = self.parent.qlist_objects.itemWidget(item)
            label_widget = None
            for ch in widget.children():
                if (ch.__class__.__name__ == 'QLabel'):
                    label_widget = ch

            label_txt = label_widget.text()
            label_split = label_txt.split('.')
            object_idx = int(label_split[0])
            self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx]['selected'] = decision
            if cbox is None:
                del item

        self.loadImage(self.parent.logs[self.parent.cntr]['path'])

    def addObject(self):
        object_type, done = QInputDialog.getText(self.parent, 'Input Dialog', 'Enter new object')

        if done is True and object_type != '':
            hlayout = QHBoxLayout()
            num_instances = len(self.parent.json_data['samples'][self.parent.cntr]['instances'])
            object_label = str(num_instances) + '.' + object_type
            obj_type_label = QLabel()
            obj_type_label.setText(object_label)
            hlayout.addWidget(obj_type_label)

            tbox = QLineEdit()
            tbox.setText('0')
            hlayout.addWidget(tbox)

            obj_dict = {}
            obj_dict['selected'] = True
            obj_dict['instance_count'] = 0
            obj_dict[object_type] = []
            self.parent.json_data['samples'][self.parent.cntr]['instances'].append(obj_dict)

            hlayout.addStretch()
            hlayout.setSizeConstraint(QLayout.SetFixedSize)
            widget = QWidget()
            widget.setLayout(hlayout)
            itemN = QListWidgetItem()
            itemN.setSizeHint(widget.sizeHint())
            self.parent.qlist_objects.addItem(itemN)
            self.parent.qlist_objects.setItemWidget(itemN, widget)

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