# importing 
import imageio.v3 as iio
import matplotlib.pyplot as plt
import cv2

import sys
import numpy as np

from SETTINGS import ImageProcessingSettings

class ImageProcessingWork:
   # @staticmethod
    
    def __init__(self, settings):
        self.settings = settings
        pass

    def high_pass_filter(self, frame):
        # Simple high-pass kernel
        kernel = np.array([[-1, -1, -1], # modify to adapt with GUI menus
                           [-1,  8, -1],
                           [-1, -1, -1]])
        filtered = cv2.filter2D(frame, -1, kernel)
        return filtered

    def clahe_modification(self,frame): # Contrast Limited Adaptive Histogram Equalization 

        clip_limit = self.settings.clahe_clip
        tile_size = (self.settings.clahe_tile, self.settings.clahe_tile)
        LAB = self.settings.clahe_lab # True = LAB, False = HSV
        
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size) # initialize CLAHE using the clip limit and tile size

        if LAB == True: # use CLAHE on LAB (Lightness, Green/Red Axis, Blue/Yellow axis).
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l_clahe = clahe.apply(l)
            lab_clahe = cv2.merge((l_clahe, a, b))
            result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

        else: # use CLAHE on HSV (Hue, Saturation, Value)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            v_clahe = clahe.apply(v)
            hsv_clahe = cv2.merge((h,s,v_clahe))
            result = cv2.cvtColor(hsv_clahe, cv2.COLOR_HSV2BGR)

        return result

    def rgb_modification(self, frame):
        # Modifies the RGB channels in the frame

        # color = int(image[300, 300])
        # if image type is b g r, then b g r value will be displayed.
        # if image is gray then color intensity will be displayed.

        modified = frame # Change to how image is modified

        return modified
    

    
    def segment(self, frame):

        segment_image = frame # change
        return segment_image
