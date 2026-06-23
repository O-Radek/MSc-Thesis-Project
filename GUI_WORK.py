# Code originally inspired byhttps://www.pythonguis.com/pyside6-tutorial/ and Dr. Nik

        # FUTURE: QGroupBox for UI!
        # Overlay processes (like edge detection(canny ?)) on image, RGB color separating, 
        # video processing

        # work on updating thesis paper. Not more than a day a week!


import sys
import cv2
from matplotlib import container
import numpy as np

#from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QEventLoop, QSize, QTimer, Qt
from PySide6.QtGui import QIcon, QPixmap, QAction, QImage

from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFileSystemModel,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTimeEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from pathlib import Path

from layout_colorwidget import Color

from SETTINGS import ImageProcessingSettings
from PROJECT import ImageProcessingWork


class ProcessingPipeline: # a class to handle the image processing pipeline based on the settings
    def __init__(self, settings):

        self.settings = settings
        self.processor = ImageProcessingWork(settings)


    def process_image(self, image):
        processed = image.copy() # making a copy of the image to then process

        if self.settings.high_pass:
            processed = self.processor.high_pass_filter(processed)

        if self.settings.clahe:
            processed = self.processor.clahe_modification(processed)

        # Add more processing steps here based on other settings
        return processed

class ImageProcessingWindow(QWidget): # create a new class for the image processing options window
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        #self.settings = ImageProcessingSettings()

        self.setWindowTitle("Image Processing Options")

        layout = QVBoxLayout()

        self.HighPassFilterButton = QCheckBox("High-Pass Filter") # create a checkbox for the high-pass filter option
        self.HighPassFilterButton.toggled.connect(self.high_pass_toggled)

        self.CLAHEButton = QCheckBox("Contrast Limited Adaptive Histogram Equalization (CLAHE)") # create a checkbox that will show/hide the slider and spinbox when toggled
        self.CLAHEButton.toggled.connect(self.clahe_toggled)
        self.CLAHEClipInput = QDoubleSpinBox() # spin box to set the clip limit
        self.CLAHEClipInput.setRange(1.0, 5.0)
        self.CLAHEClipInput.setDecimals(1)
        self.CLAHEClipInput.setSingleStep(1)
        self.CLAHEClipInput.setValue(1.0)
        self.CLAHEClipInput.valueChanged.connect(self.clahe_clip_changed)
        self.CLAHEClipInput.hide()
        self.CLAHETileSize = QComboBox() # dropdown menu to set the tile size
        self.CLAHETileSize.addItems(['4.0 x 4.0', '8.0 x 8.0', '16.0 x 16.0'])
        self.CLAHETileSize.currentIndexChanged.connect(self.clahe_tile_index_changed)
        self.CLAHETileSize.hide()
        self.LABclahe = QRadioButton("LAB")
        self.HSVclahe = QRadioButton("HSV")
        self.LABorHSV = QButtonGroup(self)
        self.LABorHSV.addButton(self.LABclahe)
        self.LABorHSV.addButton(self.HSVclahe)
        self.LABorHSV.setExclusive(True)
        self.LABclahe.setChecked(True)
        self.LABorHSV.buttonClicked.connect(self.LabHsv_Buttons)
        self.LABclahe.hide()
        self.HSVclahe.hide()

        layout.addWidget(self.HighPassFilterButton) # adding the options to the layout
        layout.addWidget(self.CLAHEButton)
        layout.addWidget(self.CLAHEClipInput)
        layout.addWidget(self.CLAHETileSize)
        layout.addWidget(self.LABclahe)
        layout.addWidget(self.HSVclahe)
        
        self.setLayout(layout) # set the layout of the window to the vertical layout we created

 
    def high_pass_toggled(self, checked):
        self.settings.high_pass = checked

    def clahe_toggled(self, checked):
        self.settings.clahe = checked
        self.CLAHEClipInput.setVisible(not self.CLAHEClipInput.isVisible())
        self.CLAHETileSize.setVisible(not self.CLAHETileSize.isVisible())
        self.LABclahe.setVisible(not self.LABclahe.isVisible())
        self.HSVclahe.setVisible(not self.HSVclahe.isVisible())

    def clahe_clip_changed(self, value):
        self.settings.clahe_clip = int(value)

    def clahe_tile_index_changed(self, index):
        if index == 0:
            self.settings.clahe_tile = 4
        elif index == 1:
            self.settings.clahe_tile = 8
        else: self.settings.clahe_tile = 16

    def LabHsv_Buttons(self, button):
        if button == self.LABclahe:
            self.mode = "LAB"
            self.settings.clahe_lab = True
        elif button == self.HSVclahe:
            self.mode = "HSV"
            self.settings.clahe_lab = False 

class CameraSourceWidget(QWidget): # create a separate class for the camera source widget
    def __init__(self, settings):
        super().__init__()
        self.cap = cv2.VideoCapture(1) # 0 = front camera, 1 = back camera

        #self.settings = ImageProcessingSettings()
        self.settings = settings
        self.pipeline = ProcessingPipeline(self.settings)

        pauseButton = QPushButton("Pause Camera")
        pauseButton.setFixedSize(QSize(200, 100)) # set the size of the button to 200x100 pixels
        pauseButton.setCheckable(True) # make the button checkable
        pauseButton.toggled.connect(self.pause_camera)

        # Layout
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        left_layout.addWidget(pauseButton)
        layout.addLayout(left_layout)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # ~30 FPS

        
    def update_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            return
        
        # all in one image processing:
        #frame = self.pipeline(frame) # process the frame using the processing pipeline based on the settings
        frame = self.pipeline.process_image(frame)

        # Convert BGR → RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = frame.shape
        bytes_per_line = ch * w

        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def pause_camera(self, checked):
        if checked:
            self.timer.stop()
        else:
            self.timer.start(30)  # ~30 FPS

    def closeEvent(self, event):
        self.cap.release()
        event.accept()


class FolderSourceWidget(QWidget): # create a separate class for the KVASIR image source widget
    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        #self.settings = ImageProcessingSettings() # create an instance of the ImageProcessingSettings class to store the settings
        self.pipeline = ProcessingPipeline(self.settings)

        layout1 = QHBoxLayout() # create a horizontal layout
        layout2 = QVBoxLayout() # create a vertical layout
        layout3 = QVBoxLayout() # create a vertical layout


        layout1.setContentsMargins(0,0,0,0) # set the margins of the layout to 0
        layout1.setSpacing(20) # set the spacing between the widgets in the layout to 20

        # Creating a ComboBox (drop down menu) to display the file names of the images in the "kvasir-ulcerative-colitis" directory
        self.combo = QComboBox()

        # defining the path to the image files and adding the file names to the combo box
        self.image_files = sorted(Path("kvasir-ulcerative-colitis").glob("*.jpg"))
        for file in self.image_files:
            self.combo.addItem(file.stem)
        self.pixmap_cache = {}

        layout2.addWidget(self.combo) # add the combo box to the vertical layout
       
        nextButton = QPushButton("Next Image")
        nextButton.setFixedSize(QSize(200, 100)) 
        backButton = QPushButton("Previous Image")
        backButton.setFixedSize(QSize(200, 100))
       
        layout2.addWidget(nextButton) # add the button to the vertical layout
        layout2.addWidget(backButton) # add the button to the vertical layout

        autoButton = QPushButton("Automatically  Advance Image")
        autoButton.setFixedSize(QSize(200, 100)) 
        autoButton.setCheckable(True) # make the button checkable
        self.autoAdvance_timer = QTimer()
        self.autoAdvance_timer.timeout.connect(self.next_image)
        self.autoAdvance_timer.setInterval(2000)  # 2 second interval for automatic image advancement
        layout2.addWidget(autoButton) # add the button to the vertical layout

        layout1.addLayout(layout2)

        self.exampleImage = QLabel()
        self.exampleImage.setAlignment(Qt.AlignCenter)
        self.exampleImage.setScaledContents(False)

        layout1.addWidget(self.exampleImage) # we can add stretch to the image.. but that would eliminate the colors to the right

        # colors as place holders, if more settings want to be included
        layout3.addWidget(Color('red'))
        layout3.addWidget(Color('yellow'))
        layout1.addLayout( layout3 )

        self.setLayout(layout1)

        # loading first image
        if self.image_files:
            self.combo.setCurrentIndex(0)
            self.update_image(0)

        self.combo.currentIndexChanged.connect(self.update_image) # connect the currentIndexChanged signal of the combo box to the update_image method
        nextButton.clicked.connect(self.next_image) # connect the clicked signal of the button to the next_image method
        backButton.clicked.connect(self.previous_image) # connect the clicked signal of the button to the previous_image method
        autoButton.toggled.connect(self.toggle_auto_advance) # connect the toggled signal of the button to the toggle_auto_advance method

        # Timer for updating image (for image processing on the current image)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(
            lambda: self.update_image(self.combo.currentIndex())
        )        
        self.refresh_timer.start(500)  # ~2 FPS
      
    def toggle_auto_advance(self, checked):
        if checked:
            self.autoAdvance_timer.start()
        else:
            self.autoAdvance_timer.stop()

    def next_image(self): # method to go to the next image in the combo box
        current_index = self.combo.currentIndex()
        next_index = (current_index + 1) % self.combo.count() # calculate the next index, wrapping around to the beginning if necessary
        self.combo.setCurrentIndex(next_index) # set the combo box to the next index, which will trigger the update_image method
        self.refresh_image() # refresh the image displayed in the QLabel

    def previous_image(self): # method to go to the previous image in the combo box
        current_index = self.combo.currentIndex()
        previous_index = (current_index - 1) % self.combo.count() # calculate the previous index, wrapping around to the end if necessary
        self.combo.setCurrentIndex(previous_index) # set the combo box to the previous index, which will trigger the update_image method
        self.refresh_image() # refresh the image displayed in the QLabel

    def update_image(self, index): # update the image displayed in the QLabel based on the selected index of the combo box
        # filling the queue and setting the path
        path = self.image_files[index]
        if path not in self.pixmap_cache:
            self.pixmap_cache[path] = QPixmap(str(path))

        frame = cv2.imread(str(path)) # converting to image information to be manipulated
        frame = self.pipeline.process_image(frame) # all in one image processing 

        # convert back for display
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

        self.exampleImage.setPixmap(QPixmap.fromImage(qimg)) # final image to be displayed


    def refresh_image(self): # refresh the image displayed in the QLabel
        if self.image_files:
            self.update_image(self.combo.currentIndex())
    
    def resizeEvent(self, event): # resize the image when the window is resized
        super().resizeEvent(event)
        self.refresh_image()
        
class MainWindow(QMainWindow):
    def __init__(self):
        # Initial setup:
        super().__init__()
        
        self.setWindowTitle("My App")
        self.settings = ImageProcessingSettings()
        self.ImProcessWindow = ImageProcessingWindow(self.settings) # create an instance of the ImProcessingWindow class to be used as a separate window 
        #self.processor = ImageProcessing()

        layout1 = QHBoxLayout() # create a horizontal layout
        layout2 = QVBoxLayout() # create a vertical layout

        # Toolbar and menu bar setup:
        toolbar = self.addToolBar("My Toolbar") # create a toolbar and add it to the main window
        toolbar.setMovable(False) # make the toolbar immovable
        toolbar.setIconSize(QSize(16, 16)) # set the icon size of the toolbar
        self.addToolBar(toolbar) # add the toolbar to the main window

        imgProcess_button = QAction(QIcon("bug.png"), "&Image Processing Settings", self) # create an action for the toolbar with an icon and text
        imgProcess_button.setStatusTip("This is your button") # set the status tip of the action
        imgProcess_button.triggered.connect(self.toolbar_button_clicked) # connect the triggered signal of the action to the toolbar_button_clicked method
        imgProcess_button.setCheckable(True) # make the action checkable
        toolbar.addAction(imgProcess_button) # add the action to the toolbar
        toolbar.addSeparator() # add a separator to the toolbar

        bug_button2 = QAction(QIcon("bug.png"), "&Your button 2", self) # create another action for the toolbar with an icon and text
        bug_button2.setStatusTip("This is your button 2") # set the status
        # bug_button2.triggered.connect(self.toolbar_button_clicked) # connect the triggered signal of the action to the toolbar_button_clicked method
        bug_button2.setCheckable(True) # make the action checkable
        toolbar.addAction(bug_button2) # add the action to the toolbar

        menu = self.menuBar() # create a menu bar and add it to the main window
        file_menu = menu.addMenu("&File") # create a "File" menu and add it to the menu bar
        file_menu.addAction(imgProcess_button) # add the first action to the "File"
        file_menu.addSeparator() # add a separator to the "File" menu
        file_submenu = file_menu.addMenu("Submenu") # create a submenu and add it to the "File" menu
        file_submenu.addAction(bug_button2) # add the second action to the submenu

        # What the GUI displays: 
        imSourceWidget = QListWidget() # create a list widget to display the image options (image folder, camera, etc.)
        imSourceWidget.addItems(["KVASIR Image Folder", "Camera"]) 
        imSourceWidget.setFixedWidth(200) # set the width of the list widget to 200 pixels

        self.stack = QStackedWidget()
        
        layout2.addWidget(imSourceWidget) # add the list widget to the vertical layout
        layout1.addLayout(layout2) # add the vertical layout to the horizontal layout

        self.stack = QStackedWidget()

        self.folderWidget = FolderSourceWidget(self.settings)
        self.cameraWidget = CameraSourceWidget(self.settings)
        
        self.stack.addWidget(self.folderWidget) # add the FolderSourceWidget to the stacked widget
        self.stack.addWidget(self.cameraWidget) # add the CameraSourceWidget to the stacked widget
        self.stack.setCurrentIndex(0) # initial index, 0 = folder, 1 = camera

        imSourceWidget.currentRowChanged.connect(
            self.stack.setCurrentIndex
        )

        layout1.addWidget(self.stack) # add the stacked widget to the horizontal layout

        container = QWidget()
        container.setLayout(layout1)

        self.setCentralWidget(container)
    
    def toolbar_button_clicked(self, checked): # temporary. To be replaced with image processing options and such
        print("Toolbar button clicked! Checked:", checked)

        if self.ImProcessWindow.isVisible():
            self.ImProcessWindow.hide()
        else:
            self.ImProcessWindow.show()

        


