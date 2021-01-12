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

import pyqtgraph as pg
pg.setConfigOptions(imageAxisOrder='row-major')

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
        
        nframes,nplanes,nchans,W,H = self.mmap.shape
        self.nplanes = nplanes
        self.nframes = nframes
        self.initUI()
        
    def initUI(self):
        # Menu
        bar = self.menuBar()
        editmenu = bar.addMenu("Experiment")
        editmenu.addAction("New")
        #editmenu.triggered[QAction].connect(self.experimentMenuTrigger)
        self.setWindowTitle("Scanbox viewer")
        self.tabs = []
        self.widgets = []
        self.tabs.append(QDockWidget("Imaging plane",self))
        self.widgets.append(ImageViewerWidget(self,self.mmap))
        self.tabs[-1].setWidget(self.widgets[-1])
        self.tabs[-1].setFloating(False)
        #self.tabs[-1].setFixedWidth(self.mmap.shape[3])
        #self.tabs[-1].setFixedHeight(self.mmap.shape[4])
        self.addDockWidget(
            Qt.RightDockWidgetArea and Qt.TopDockWidgetArea,
            self.tabs[-1])
        c = 1
        self.controlWidget = ControlWidget(self)
        self.tabs.append(QDockWidget("Frame control",self))
        self.tabs[-1].setWidget(self.controlWidget)
        self.tabs[-1].setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea,self.tabs[-1])
        self.timer = QTimer()
        self.timer.timeout.connect(self.timerUpdate)
        self.timer.start(0.01)
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
        self.frameSlider.setMaximum(self.parent.mmap.shape[0])
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
        self.frameSliderLabel.setText('Frame [{0}]:'.format(int(value)))
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
        frame = self.sbxdata[0,:,0,:,:].squeeze()
        self.nplanes = parent.nplanes
        self.string = '# {0}'
        self.stringShift = '# {0} - shift ({1:1.1f},{2:1.1f})'
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        toggleSubtract = QAction("Background subtraction",self)
        toggleSubtract.triggered.connect(self.toggleSubtract)
        self.addAction(toggleSubtract)
        self.win = pg.GraphicsLayoutWidget()
        grid = QFormLayout()
        grid.addRow(self.win)
        self.setLayout(grid)
        p1 = self.win.addPlot(title="")
        p1.getViewBox().invertY(True)
        p1.hideAxis('left')
        p1.hideAxis('bottom')
        nplanes,H,W = frame.shape
        positions = [[int(np.mod(i,2))*W,
                      int(i/2)*H] for i in range(self.nplanes)]
        self.imgview = [pg.ImageItem() for i in range(self.nplanes)]
        for p,img in zip(positions,self.imgview):
            img.setPos(*p)

        for img in self.imgview:
            p1.addItem(img)
        
        self.plane = 0
        self.register = False
        self.references = [None for iplane in range(self.nplanes)]
        self.update(0)
        self.show()
    def update(self,nframe):
        stack = np.array(self.sbxdata[nframe,:,0,:,:]).astype(np.float32)
        if self.register:
            for iplane in range(self.nplanes):
                if self.references[iplane] is None:
                    self.references[iplane] = 2**16 - np.squeeze(
                        self.sbxdata[:256,iplane,0,:,:].mean(axis = 0))
                shift = registration_upsample(
                    self.references[iplane][200:-200:2,200:-200:1],
                    stack[iplane][200:-200:2,200:-200:1])
                stack[iplane] = shift_image(stack[iplane],shift)
                if iplane == 0:
                    # set the shift value 
                    pass
            
        for iplane in range(self.nplanes):
            self.imgview[iplane].setImage(stack[iplane])
        self.lastnFrame = nframe
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
