from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, QPoint
import json

# subclass
class CheckableComboBox(QComboBox):
    # once there is a checkState set, it is rendered
    # here we assume default Unchecked
    #self.entry = None
    def addItem(self, item, parent=None):
        super(CheckableComboBox, self).addItem(item)
        item = self.model().item(self.count() - 1, 0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Checked)

        #if parent is not None:
        #    self.model().itemChanged.connect(parent.toggleBbox)

    def itemChecked(self, index):
        item = self.model().item(index, 0)
        return item.checkState() == QtCore.Qt.Checked

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
        self.conf = 1.0

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
        self.parent.add_instance.clicked.connect(self.addInstance)
        self.parent.update_conf.clicked.connect(self.updateConfidence)
        self.parent.save_json.clicked.connect(self.saveJson)

    def updateConfidence(self):
        text = self.parent.confidence_lineedit.text()
        try:
            self.conf = float(text)
            self.loadImage(self.parent.logs[self.parent.cntr]['path'], self.conf)
        except ValueError:
            QMessageBox.warning(self.parent, 'Input Error', 'Please enter valid float value')

    def addInstance(self):
        listItems = self.parent.qlist_objects.selectedItems()
        if listItems is None or len(listItems) == 0:
            QMessageBox.warning(self.parent, 'No object selected', 'Please select an object to add instances to')
            return
        instance, done = QInputDialog.getText(self.parent, 'Input Dialog', 'Enter new instance')

        if done is True and instance != '':
            for item in listItems:
                widget = self.parent.qlist_objects.itemWidget(item)
                for ch in widget.children():
                    if (ch.__class__.__name__ == 'CheckableComboBox'):
                        instance = str(ch.count()) + '.'+instance
                        ch.addItem(instance)
                        break


    def saveJson(self):
        #remaining_instances = []
        for index in range(self.parent.qlist_objects.count()):
            item = self.parent.qlist_objects.item(index)
            widget = self.parent.qlist_objects.itemWidget(item)
            #curr_obj_dict = {}
            label_widget = None
            combobox_widget = None
            for ch in widget.children():
                if (ch.__class__.__name__ == 'QLabel'):
                    label_widget = ch
                elif (ch.__class__.__name__ == 'CheckableComboBox'):
                    combobox_widget = ch

            label_txt = label_widget.text()
            label_split = label_txt.split('.')
            object_idx = int(label_split[0])
            object_name = label_split[1]
            #curr_obj_dict = self.parent.json_data['samples'][self.parent.cntr][object_idx]

            for i in range(combobox_widget.count()):
                instance_split = combobox_widget.itemText(i).split('.')
                instance_idx = int(instance_split[0])
                if combobox_widget.itemChecked(i):
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx][object_name][instance_idx]['selected'] = True
                else:
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx][object_name][instance_idx]['selected'] = False

            #remaining_instances.append(curr_obj_dict)

        #self.parent.json_data['samples'][self.parent.cntr]['instances'] = remaining_instances

        with open(self.parent.json_file, 'w') as outfile:
            json.dump(self.parent.json_data, outfile, indent=4)

    def onResize(self):
        ''' things to do when qlabel_image is resized '''
        self.qpixmap = QPixmap(self.qlabel_image.size())
        self.qpixmap.fill(QtCore.Qt.gray)
        self.qimage_scaled = self.qimage.scaled(self.qlabel_image.width() * self.zoomX, self.qlabel_image.height() * self.zoomX, QtCore.Qt.KeepAspectRatio)
        self.update(self.instance)

    def toggleBbox(self, item=None):
        if item is not None:
            listItems = self.parent.qlist_objects.selectedItems()
            instance_text = item.text()
            instance_idx = int(instance_text.split('.')[0])
            for itm in listItems:
                # selected = self.parent.qlist_objects.takeItem(self.parent.qlist_objects.row(item))
                widget = self.parent.qlist_objects.itemWidget(itm)
                label_widget = None
                for ch in widget.children():
                    if (ch.__class__.__name__ == 'QLabel'):
                        label_widget = ch

                label_txt = label_widget.text()
                label_split = label_txt.split('.')
                object_idx = int(label_split[0])
                object_name = label_split[1]
                if item.checkState() == QtCore.Qt.Checked:
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx][object_name][instance_idx]['selected'] = True
                else:
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][object_idx][object_name][instance_idx]['selected'] = False

            self.drawBbox(self.parent.logs[self.parent.cntr]['path'], self.conf)

    def createFilterArea(self, conf):
        instance = self.parent.json_data['samples'][self.parent.cntr]['instances']
        if self.current_instances == -1:
            self.current_instances = len(instance)

        if instance is not None:
            self.parent.qlist_objects.clear()
            for i in range(len(instance)):
                object_dict = instance[i]
                if 'selected' not in self.parent.json_data['samples'][self.parent.cntr]['instances'][i]:
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][i]['selected'] = True
                    object_dict = self.parent.json_data['samples'][self.parent.cntr]['instances'][i]

                if object_dict['selected'] is False:
                    continue

                for object_type in object_dict:
                    if object_type == 'selected':
                        continue
                    hlayout = QHBoxLayout()
                    obj_type_label = QLabel()
                    #obj_type_cbox = QCheckBox(str(i) + '.' + object_type)
                    #obj_type_cbox.setChecked(True)
                    #obj_type_cbox.stateChanged.connect(lambda: self.removeSel(obj_type_cbox))
                    obj_type_label.setText(str(i) + '.' + object_type)
                    hlayout.addWidget(obj_type_label)
                    attrib = object_dict[object_type]
                    comboBox = CheckableComboBox(self.parent)
                    comboBox.setStyleSheet('''*    
                            QComboBox QAbstractItemView 
                                {
                                min-width: 120px;
                                }
                            ''')

                    for j in range(len(attrib)):
                        params = attrib[j]
                        metadata = ''
                        if 'selected' not in params:
                            params['selected'] = True
                            self.parent.json_data['samples'][self.parent.cntr]['instances'][i][object_type][j][
                                'selected'] = True

                        if params['selected'] is False or (conf is not None and params['conf'] < conf):
                            continue

                        bbox = params["bbox"]
                        if 'metadata' in params:
                            metadata = params["metadata"]

                        if metadata != '':
                            comboBox.addItem(str(j) + '.' + params["id"] + '-' + metadata, self)
                        elif bbox is not None and len(bbox) == 4:
                            comboBox.addItem(str(j) + '.' + params["id"] + ':' + '[' + str(int(bbox[0])) + ',' + str(
                                int(bbox[1])) + ',' + str(int(bbox[2])) + ',' + str(int(bbox[3])) + ']', self)
                        else:
                            comboBox.addItem(str(j) + '.' + params["id"], self)
                    comboBox.model().itemChanged.connect(self.toggleBbox)
                    hlayout.addWidget(comboBox)

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

        if instance is not None:
            penRectangle = QPen(Qt.green)
            penRectangle.setWidth(1)
            painterInstance = QPainter(self.qimage)

            for i in range(len(instance)):
                object_dict = instance[i]
                if 'selected' not in self.parent.json_data['samples'][self.parent.cntr]['instances'][i]:
                    self.parent.json_data['samples'][self.parent.cntr]['instances'][i]['selected'] = True
                    object_dict = self.parent.json_data['samples'][self.parent.cntr]['instances'][i]

                if object_dict['selected'] is False:
                    continue

                for object_type in object_dict:
                    if object_type == 'selected':
                        continue

                    attrib = object_dict[object_type]
                    for j in range(len(attrib)):
                        params = attrib[j]
                        if params['selected'] is False or (conf is not None and params['conf'] < conf):
                            continue

                        bbox = params["bbox"]

                        penText = QPen(Qt.red)
                        painterInstance.setPen(penText)
                        painterInstance.setFont(QFont('Decorative', 8))
                        painterInstance.drawText(max(bbox[0], 50), max(bbox[1] - 20, 50), params["id"])

                        if bbox is not None and len(bbox) == 4:
                            painterInstance.setPen(penRectangle)
                            painterInstance.drawRect(bbox[0], bbox[1], bbox[2], bbox[3])

            painterInstance.end()

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
        if conf is None:
            conf = self.conf
        self.createFilterArea(conf)
        self.drawBbox(imagePath, conf)

    def removeSel(self, cbox=None):
        decision = False
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
            num_instances = self.current_instances
            self.current_instances += 1
            #new_dict[object_type] = {}
            #new_dict['selected'] = True
            #self.parent.json_data['samples'][self.parent.cntr]['instances'].append(new_dict)
            object_type = str(num_instances) + '.' + object_type
            obj_type_label = QLabel()
            obj_type_label.setText(object_type)
            hlayout.addWidget(obj_type_label)
            comboBox = CheckableComboBox(self.parent)
            hlayout.addWidget(comboBox)

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