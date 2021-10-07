
try:
    import cv2
except Exception as err:
    print('cv2 not installed, trying to install dependencies with pip ')
    from subprocess import call
    call('pip install opencv-python pyqtgraph pyqt5',shell = True)
    import cv2

import numpy as np

def registration_upsample(frame,template):
    h,w = frame.shape
    dst = frame.astype('float32')
    (xs, ys), sf = cv2.phaseCorrelate(template.astype('float32'),dst)
    return (xs,ys)


def shift_image(img,shift):
    M = np.float32([[1,0,shift[0]],[0,1,shift[1]]])
    return cv2.warpAffine(img,M,(img.shape[1],img.shape[0]))
