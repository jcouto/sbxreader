import sys
import os
import numpy as np
import time
import atexit
import argparse
from glob import glob
from time import sleep

try:
    import cv2
except Exception as err:
    print('cv2 not installed, trying to install dependencies with pip ')
    from subprocess import call
    call('pip install opencv-python pyqtgraph pyqt5',shell = True)
    import cv2

# Qt imports
from PyQt5.QtWidgets import (QWidget,
                             QApplication,
                             QGridLayout,
                             QFormLayout,
                             QVBoxLayout,
                             QTabWidget,
                             QCheckBox,
                             QTextEdit,
                             QLineEdit,
                             QComboBox,
                             QFileDialog,
                             QSlider,
                             QPushButton,
                             QLabel,
                             QAction,
                             QMenuBar,
                             QGraphicsView,
                             QGraphicsScene,
                             QGraphicsItem,
                             QGraphicsLineItem,
                             QGroupBox,
                             QTableWidget,
                             QMainWindow,
                             QDockWidget,
                             QFileDialog)
from PyQt5.QtGui import QImage, QPixmap,QBrush,QPen,QColor
from PyQt5.QtCore import Qt,QSize,QRectF,QLineF,QPointF,QTimer

def registration_upsample(frame,template):
    h,w = frame.shape
    dst = frame.astype('float32')
    (xs, ys), sf = cv2.phaseCorrelate(template.astype('float32'),dst)    
    return (ys,xs)


def shift_image(img,shift):
    M = np.float32([[1,0,shift[1]],[0,1,shift[0]]])
    return cv2.warpAffine(img,M,(img.shape[1],img.shape[0]))


from .reader import sbx_memmap

class ScanboxViewer(QMainWindow):
    app = None
    def __init__(self,fname = None,app = None):
        super(ScanboxViewer,self).__init__()
        self.app = app
        self.filename = fname
        self.mmap = sbx_memmap(self.filename)
        (nframes,nplanes,nchan,W,H) = self.mmap.shape
        self.nplanes = nplanes
        self.nframes = nframes
        self.initUI()
        
    def initUI(self):
        # Menu
        bar = self.menuBar()
        #editmenu.triggered[QAction].connect(self.experimentMenuTrigger)
        self.setWindowTitle("Scanbox viewer")
        self.tabs = []
        self.widgets = []
        self.tabs.append(QDockWidget("Imaging plane",self))
        c = 0
        layout = QVBoxLayout()
        self.widgets.append(ImageViewerWidget(self,self.mmap))
        self.tabs[-1].setWidget(self.widgets[-1])
        self.tabs[-1].setFloating(False)
        self.tabs[-1].setFixedWidth(self.mmap.shape[3])
        self.tabs[-1].setFixedHeight(self.mmap.shape[4])
        if c < 2:
            self.addDockWidget(
                Qt.RightDockWidgetArea and Qt.TopDockWidgetArea,
                self.tabs[-1])
        else:
            self.addDockWidget(
                Qt.RightDockWidgetArea and Qt.BottomDockWidgetArea,
                self.tabs[-1])
        c = 1
        self.controlWidget = ControlWidget(self)
        self.tabs.append(QDockWidget("Frame control",self))
        self.tabs[-1].setWidget(self.controlWidget)
        self.tabs[-1].setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea,self.tabs[-1])
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerUpdate)
        self.timer.start(0.03)
        self.move(0, 0)
        self.show()
    def timerUpdate(self):
        self.controlWidget.frameSlider.setValue(np.mod(self.controlWidget.frameSlider.value() + 1,self.nframes))

class ControlWidget(QWidget):
    def __init__(self,parent):
        super(ControlWidget,self).__init__()	
        self.parent = parent
        form = QFormLayout()
        self.setLayout(form)
        self.frameSlider = QSlider(Qt.Horizontal)
        self.frameSlider.setValue(0)
        self.frameSlider.setMinimum(0)
        self.frameSlider.setMaximum(self.parent.mmap.shape[-1]/self.parent.nplanes)
        self.frameSlider.setSingleStep(1)
        self.frameSliderLabel = QLabel('Frame [{0}]:'.format(self.frameSlider.value()))
        self.frameSlider.valueChanged.connect(self.setFrame)
        form.addRow(self.frameSliderLabel, self.frameSlider)

        self.playback = QCheckBox()
        self.playback.setChecked(True)
        self.playback.stateChanged.connect(self.togglePlayback)
        form.addRow(QLabel("Playback: "),self.playback)
        self.register = QCheckBox()
        self.register.setChecked(False)
        self.register.stateChanged.connect(self.toggleRegister)
        form.addRow(QLabel("Register: "),self.register)

    def setFrame(self,value):
        self.parent.widgets[0].update(int(value))

    def setPlane(self,value):
        iPlane = self.planeSelector.currentIndex()
        self.parent.widgets[0].plane = iPlane
        self.parent.widgets[0].update(int(self.frameSlider.value()))
        
    def togglePlayback(self,value):
        if value:
            self.parent.timer.start()
        else:
            self.parent.timer.stop()
    def toggleRegister(self,value):
        self.parent.widgets[0].register = value

class ImageViewerWidget(QWidget):
    def __init__(self,parent,sbxdata,parameters = dict(backgroundSubtract=False)):
        super(ImageViewerWidget,self).__init__()
        self.sbxdata = sbxdata
        frame = np.array(self.sbxdata[0,:,0,:,:])
        print(frame.shape)
        self.nplanes = parent.nplanes
        self.string = '# {0}'
        self.stringShift = '# {0} - shift ({1:1.1f},{2:1.1f})'
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        toggleSubtract = QAction("Background subtraction",self)
        toggleSubtract.triggered.connect(self.toggleSubtract)
        self.addAction(toggleSubtract)
        self.scene=QGraphicsScene(0,0,frame.shape[-1],
                                  frame.shape[-2],self)
        self.view = QGraphicsView(self.scene, self)
        self.plane = 0
        self.register = False
        self.references = [None for iplane in range(self.nplanes)]
        self.update(1)
        self.show()
    def update(self,nframe):
        self.scene.clear()
        i = int(nframe)
        image = np.array(np.squeeze(self.sbxdata[i,:,0,:,:]))
        frame = 255 - cv2.convertScaleAbs(image, alpha=(255.0/65535.0))
        if self.register:
            if self.references[self.plane] is None and not nframe == 0:
                stack = self.sbxdata[:400,::self.nplanes,0].mean(axis = 0)
                self.references[self.plane] = 255 - cv2.convertScaleAbs(
                    stack.T,
                    alpha=(255.0/65535.0))
            shift,_,_ = registration_upsample(
                self.references[self.plane][200:-200:2,200:-200:1],
                frame[200:-200:2,200:-200:1],
                upsample_factor=2)
            frame = shift_image(frame,shift)
        frame = cv2.cvtColor(frame.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        if self.register:
            cv2.putText(frame,self.stringShift.format(i,
                                                      shift[0],
                                                      shift[1]),
                        (10,100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, [200,0,0],2)
        else:
            cv2.putText(frame,self.string.format(i), (10,100),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, [200,0,0],2)

        self.qimage = QImage(frame, frame.shape[1], frame.shape[0], 
                             frame.strides[0], QImage.Format_RGB888)
        self.scene.addPixmap(QPixmap.fromImage(self.qimage))
        self.lastnFrame = nframe
        self.scene.update()
    def toggleSubtract(self):
        pass

def main():
    parser = argparse.ArgumentParser(description='Scanbox raw data viewer.')
    parser.add_argument('fname',
                        metavar = 'fname',
                        type = str,
                        help = 'Scanbox filename path.')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    target = None
    if os.path.isfile(args.fname):
        target = args.fname
    params = None

    w = ScanboxViewer(target,app = app)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
