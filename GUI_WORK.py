# Code originally inspired by https://www.pythonguis.com/pyside6-tutorial/ and Dr. Nik

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from PROJECT import ImageProcessingWork
from SETTINGS import ImageProcessingSettings


class ProcessingPipeline: # a class to handle the image processing pipeline based on the settings
    def __init__(self, settings):

        self.settings = settings # store the settings object
        self.processor = ImageProcessingWork(settings) # create an instance of the ImageProcessingWork class to handle the actual image processing


    def process_image(self, image):
        processed = image.copy() # making a copy of the image to then process

        # Note- Only one setting is active at a time. 
        if self.settings.clahe:
            processed = self.processor.clahe_modification(processed)        

        if self.settings.denoise:
            processed = self.processor.noise_reduction(processed)
        
        if self.settings.high_pass:
            processed = self.processor.high_pass_filter(processed)

        if self.settings.rgb:
            processed = self.processor.rgb_modification(processed)

        if self.settings.threshold:
            processed = self.processor.thresholding(processed)

        if self.settings.txi:
            processed = self.processor.txi_modification(processed)

        processed = np.clip(processed, 0, 255).astype(np.uint8) # force the output to be a uint8 image, as some of the processing methods may produce values outside the range of 0-255. This ensures that the output image is valid and can be displayed correctly.

        return processed
    

class ImageProcessingWindow(QWidget): # The window for the image processing settings 
    DEFAULT_TXI = { # default values for the TXI settings, used when the "Use Default Settings" checkbox is checked
        "alpha": 1.4,
        "gamma": 2.2,
        "enhancement": 1.2,
        "s1": 15,
        "s2": 30,
        "t1": 5,
        "t2": 30,
    }
    
    def __init__(self, settings):
        super().__init__()

        self.settings = settings # store the settings object
        self.setWindowTitle("Image Processing Options") 
        self.setFixedSize(500, 700)

        self._build_window() # Build the window layout and widgets
        self._build_clahe()
        self._build_denoising()
        self._build_high_pass()
        self._build_rgb()
        self._build_threshold()
        self._build_txi()

        self._build_layout() # Build the entire layout

        self.processing_groups = [ # store the processing groups in a list for easy access and management
            self.HighPassGroup,
            self.CLAHEGroup,
            self.RGBGroup,
            self.ThresholdGroup,
            self.DenoiseGroup,
            self.TXIGroup,
        ]


    # ==========================================================
    # Helper Methods
    # ==========================================================
    def _add_widgets(self, widgets): # Helper method to add widgets to the layout
        for widget in widgets:
            self.layout.addWidget(widget)

    def _button_mapping(self, group): # Helper method to map buttons in a QButtonGroup to their index
        """Return {button: index} for a QButtonGroup."""
        return {
            button: i
            for i, button in enumerate(group.buttons())
        }

    def _collapse_other_groups(self, active_group): # Helper method to collapse other processing groups when one is activated, ensuring only one processing method is active at a time
        for group in self.processing_groups:
            if group is not active_group and group.isChecked():
                group.setChecked(False)

    def _slider(self, minimum, maximum, value): # Helper method to create a QSlider with specified minimum, maximum, and initial value
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setSingleStep(1)
        slider.setValue(value)
        return slider


    # ==========================================================
    # Build CLAHE
    # ==========================================================

    def _build_clahe(self):

        self.CLAHEGroup, layout = self._create_section("CLAHE") # create a group box for the CLAHE settings
        self.CLAHEGroup.toggled.connect(self.clahe_toggled) # connect the toggled signal of the group box to the clahe_toggled method

        self.CLAHEClipInput = QDoubleSpinBox() # creating the clip input widget: a spin box with value options ranging from 1 - 5 with 0.1 increments
        self.CLAHEClipInput.setRange(1.0, 5.0)
        self.CLAHEClipInput.setDecimals(1)
        self.CLAHEClipInput.setSingleStep(0.1)
        self.CLAHEClipInput.setValue(1.0)
        self.CLAHEClipInput.valueChanged.connect(self.clahe_changed)

        self.CLAHETileSize = QComboBox() # creating the tile size widget: a drop down menu with three options: 4x4, 8x8, 16x16
        self.CLAHETileSize.addItems([
            "4 × 4",
            "8 × 8",
            "16 × 16",
        ])
        self.CLAHETileSize.currentIndexChanged.connect(self.clahe_changed)

        self.LABclahe = QRadioButton("LAB") # creating the color space selection widget: radio buttons for LAB or HSV. Radio buttons allow for only one to be selected at a time
        self.HSVclahe = QRadioButton("HSV")

        self.LABorHSV = QButtonGroup(self)
        self.LABorHSV.addButton(self.LABclahe)
        self.LABorHSV.addButton(self.HSVclahe)
        self.LABclahe.setChecked(True)
        self.LABorHSV.buttonClicked.connect(self.clahe_changed)

        layout.addRow("Clip Limit", self.CLAHEClipInput)
        layout.addRow("Tile Size", self.CLAHETileSize)

        modeLayout = QHBoxLayout() # creating a horizontal layout for the radio buttons, having them sit side by side
        modeLayout.addWidget(self.LABclahe)
        modeLayout.addWidget(self.HSVclahe)

        layout.addRow("Colour Space", modeLayout)


    # ==========================================================
    # Build Denoising
    # ==========================================================

    def _build_denoising(self):

        self.DenoiseGroup, layout = self._create_section( # create a group box for Denoising
            "Non-Local Means Denoising"
        )
        self.DenoiseGroup.toggled.connect( # connect the toggled signal of the group box to the denoising_toggled method
            self.denoising_toggled
        )

        self.LumLabel = QLabel("Luminance Strength") # create the text labels for Luminance Strength, Color Strength, and Patch and Window Size
        self.ColLabel = QLabel("Color Strength")
        self.patchLabel = QLabel("Template Patch Size")
        self.searchLabel = QLabel("Search Window Size")

        self.lumBox = QDoubleSpinBox() # create the spin boxes for Luminance Strength, Color Strength, and Patch and Window Size
        self.lumBox.setRange(0, 30)
        self.lumBox.setDecimals(2)
        self.lumBox.setSingleStep(0.25)
        self.lumBox.setValue(10)

        self.colBox = QDoubleSpinBox()
        self.colBox.setRange(0, 30)
        self.colBox.setDecimals(2)
        self.colBox.setSingleStep(0.25)
        self.colBox.setValue(10)

        self.patchBox = QSpinBox()
        self.patchBox.setRange(3, 11)
        self.patchBox.setSingleStep(2) # Patch and Window size can only be odd values, thus the step size for them is 2
        self.patchBox.setValue(7)

        self.searchBox = QSpinBox()
        self.searchBox.setRange(11, 35)
        self.searchBox.setSingleStep(2)
        self.searchBox.setValue(15)

        for widget in ( # for the denoising setting widgets, connect them to the denoising value update method when any value changes, which will update the settings object with the new values
            self.lumBox,
            self.colBox,
            self.patchBox,
            self.searchBox,
        ):
            widget.valueChanged.connect(
                self.denoise_values_updated
            )

        layout.addRow(self.LumLabel, self.lumBox)
        layout.addRow(self.ColLabel, self.colBox)
        layout.addRow(self.patchLabel, self.patchBox)
        layout.addRow(self.searchLabel, self.searchBox)


    # ==========================================================
    # Build High Pass Filter
    # ==========================================================

    def _build_high_pass(self):

        self.HighPassGroup, layout = self._create_section("High Pass Filter")
        self.HighPassGroup.toggled.connect(
            self.high_pass_toggled
        )

        self.HighPassSlider = self._slider(60, 120, 80) # create a slider for the High Pass Filter intensity, with a range of 6.0 to 12.0 (scaled by 10 for the slider) and an initial value of 8.0
        self.HighPassSlider.sliderReleased.connect( # when the slider changes value, connect it to the high_pass_changed method, which will update the settings object and GUI display with the new value 
            self.high_pass_changed
        )
        self.HighPassSlider.sliderReleased.connect(
            self.high_pass_changed
        )

        self.HighPassLabel = QLabel("HPF Intensity = 8.0") # set the initial HPF label 

        layout.addRow(self.HighPassLabel)
        layout.addRow(self.HighPassSlider)


    # ==========================================================
    # Build RGB Gain
    # ==========================================================

    def _build_rgb(self):

        self.RGBGroup, layout = self._create_section("RGB Gain")
        self.RGBGroup.toggled.connect(self.rgb_toggled)

        self.RedSlider = self._slider(0, 200, 100) # initialize the sliders for Red, Green, and Blue with a range of 0 to 200% and an initial value of 100% (AKA- no change)
        self.GreenSlider = self._slider(0, 200, 100)
        self.BlueSlider = self._slider(0, 200, 100)

        self.RedLabel = QLabel("Red Intensity = 100%")
        self.GreenLabel = QLabel("Green Intensity = 100%")
        self.BlueLabel = QLabel("Blue Intensity = 100%")

        for slider in ( # connect the sliders to the rgb_updates method, which will update the settings object and GUI display with the new values when any slider is released
            self.RedSlider,
            self.GreenSlider,
            self.BlueSlider,
        ):
            slider.sliderReleased.connect(self.rgb_updates)

        layout.addRow(self.RedLabel, self.RedSlider)
        layout.addRow(self.GreenLabel, self.GreenSlider)
        layout.addRow(self.BlueLabel, self.BlueSlider)


    # ==========================================================
    # Build Thresholding
    # ==========================================================

    def _build_threshold(self):

        self.ThresholdGroup, layout = self._create_section("Threshold")
        self.ThresholdGroup.toggled.connect(self.threshold_toggled)

        self.ThresholdValue = QSpinBox() # create the threshold value widget, a spin box with a range of 0 to 255 and an initial value of 127
        self.ThresholdValue.setRange(0, 255)
        self.ThresholdValue.setValue(127)
        self.ThresholdValue.valueChanged.connect(
            self.threshold_update
        )

        threshold_names = [ # create the list of thresholding methods for the radio buttons
            "Binary",
            "Inverse Binary",
            "Truncate",
            "To Zero",
            "To Zero Inverse",
            "Otsu's Method",
        ]

        self.ThreshChoice = QButtonGroup(self)
        self.threshold_buttons = []

        for name in threshold_names: # create the radio buttons for the thresholding methods and add them to the button group and the layout
            button = QRadioButton(name)
            self.ThreshChoice.addButton(button)
            self.threshold_buttons.append(button)

        self.BinThresh = self.threshold_buttons[0] # store references to the individual thresholding method buttons for the threshold_update method to use when updating the settings object
        self.InvBinThresh = self.threshold_buttons[1]
        self.TruncThresh = self.threshold_buttons[2]
        self.ZeroThresh = self.threshold_buttons[3]
        self.InvZeroThresh = self.threshold_buttons[4]
        self.OtsuThresh = self.threshold_buttons[5]

        self.BinThresh.setChecked(True) # set the Binary Thresholding function as the initial function

        self.ThreshChoice.buttonClicked.connect(
            self.threshold_update
        )

        self.OtsuVal = QLabel("Otsu's Method Threshold Value = N/A") # create a label to display the threshold value calculated by Otsu's method, which will be updated when Otsu's method is selected and applied

        layout.addRow("Threshold", self.ThresholdValue)

        for button in self.threshold_buttons:
            layout.addRow(button)

        layout.addRow(self.OtsuVal)


    # ==========================================================
    # Build TXI
    # ==========================================================

    def _build_txi(self):

        self.TXIGroup, layout = self._create_section( # create a group box for TXI
            "TXI (Texture and Intensity)"
        )
        self.TXIGroup.toggled.connect(self.txi_toggled) # if the group box is toggled, connect it to the txi_toggled method

        self.TXIDefaultButton = QCheckBox("Use Default Settings") # create a checkbox for using the default TXI settings, which will override any custom settings when checked
        self.TXIDefaultButton.toggled.connect(self.txi_default)

        self.AlphaLabel = QLabel("Alpha") # create the labels for the alpha, gamma, and enhancement values
        self.GammaLabel = QLabel("Gamma")
        self.EnhancementLabel = QLabel("Enhancement")

        self.TXIAlpha = QDoubleSpinBox() # create the spin box for alpha, which has a range of 1 - 2 and step size 0.1. Sato's paper uses the default of 1.4
        self.TXIAlpha.setRange(1.0, 2.0)
        self.TXIAlpha.setSingleStep(0.1)
        self.TXIAlpha.setValue(1.4)

        self.TXIGamma = QDoubleSpinBox() # create the spin box for gamma, which has a range of 1-4 and step size 0.1. Sato's paper was vague on the gamma value. 
        self.TXIGamma.setRange(1.0, 4.0)
        self.TXIGamma.setSingleStep(0.1)
        self.TXIGamma.setValue(2.2) # 2.2 is used, following the industry standard value

        self.TXIEnhancement = QDoubleSpinBox() # create the spin box for alpha, which has a range of 1 - 3 and step size 0.1. Sato's paper uses the default of 1.2
        self.TXIEnhancement.setRange(1.0, 2.0)
        self.TXIEnhancement.setSingleStep(0.1)
        self.TXIEnhancement.setValue(1.2)

        # create the labels for s1, s2, t1, and t2, which are parameters for TXI color enhancement
        self.s1Label = QLabel("s1 (Lower Color Enhancement Threshold)") 
        self.s2Label = QLabel("s2 (Upper Color Enhancement Threshold)")
        self.t1Label = QLabel("t1 (Initial Color Boost)")
        self.t2Label = QLabel("t2 (Maximum Color Boost)")

        self.txiS1 = QSpinBox()
        self.txiS2 = QSpinBox()
        self.txiT1 = QSpinBox()
        self.txiT2 = QSpinBox()

        # configure the ranges for s1, s2, t1, and t2. The ranges are set to ensure that s1 < s2 and t1 < t2 for the upper and lower extremes, as required by the TXI algorithm.
        self.txiS1.setRange(15, 49) 
        self.txiS2.setRange(16, 50)
        self.txiT1.setRange(0, 49)
        self.txiT2.setRange(1, 50)

        # setting the initial values as the values Sato used in the paper
        self.txiS1.setValue(15) 
        self.txiS2.setValue(30)
        self.txiT1.setValue(5)
        self.txiT2.setValue(30)

        for widget in ( # if any widget in TXI changes its value, connect to the txi_changed def to update the values in the settings
            self.TXIAlpha,
            self.TXIGamma,
            self.TXIEnhancement,
            self.txiS1,
            self.txiS2,
            self.txiT1,
            self.txiT2,
        ):
            widget.valueChanged.connect(
                self.txi_changed
            )

        layout.addRow(self.TXIDefaultButton)

        layout.addRow(self.AlphaLabel, self.TXIAlpha)
        layout.addRow(self.GammaLabel, self.TXIGamma)
        layout.addRow(self.EnhancementLabel, self.TXIEnhancement)
        layout.addRow(self.s1Label, self.txiS1)
        layout.addRow(self.s2Label, self.txiS2)
        layout.addRow(self.t1Label, self.txiT1)
        layout.addRow(self.t2Label, self.txiT2)


    # ==========================================================
    # Window Layout
    # ==========================================================

    def _build_window(self):

        self.scroll = QScrollArea() # create a scroll area, allowing for scrolling through the settings if the window is too small
        self.scroll.setWidgetResizable(True) # set the scroll area to resize with the window, ensuring that the contents are always visible and accessible

        self.container = QWidget() # create a container widget to hold the layout and widgets for the settings window

        self.layout = QVBoxLayout(self.container) # create a vertical layout for the container widget, allowing for stacking the settings widgets vertically
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.scroll.setWidget(self.container) # set the container widget as the scroll area's widget, allowing for scrolling through the settings if the window is too small

        window_layout = QVBoxLayout(self) # create a vertical layout for the main window, allowing for stacking the scroll area and other widgets vertically
        window_layout.addWidget(self.scroll)

    def _create_section(self, title): # helper method to create a group box for a section of the settings window, allowing for grouping related settings together and providing a title for the section

        group = QGroupBox(title)
        group.setCheckable(True)
        group.setChecked(False)

        layout = QFormLayout(group)

        return group, layout

    def _build_layout(self): # add all image processing setting groups to the window

        self._add_widgets([
            self.CLAHEGroup,
            self.DenoiseGroup,
            self.HighPassGroup,           
            self.RGBGroup,
            self.ThresholdGroup,
            self.TXIGroup,
        ])

# ==========================================================
# CLAHE Helpers
# ==========================================================
    def clahe_toggled(self, checked):
        self.settings.clahe = checked
        if checked:
            self.settings.active_processing = "CLAHE" # set CLAHE as the active setting
            self._collapse_other_groups(self.CLAHEGroup) # set other image processing settings as unchecked / unactivated

    def clahe_changed(self):
        self.settings.clahe_clip = self.CLAHEClipInput.value()
        self.settings.clahe_tile = (4, 8, 16)[self.CLAHETileSize.currentIndex()] # set the tile size based on the index of the selected option in the drop down menu
        self.settings.clahe_lab = self.LABclahe.isChecked() # set the color space based on the selected radio button (LAB or HSV), True = LAB, False = HSV

# ==========================================================
# Denoising Helpers
# ==========================================================
    def denoising_toggled(self, checked):
        self.settings.denoise = checked

        if checked:
            self.settings.active_processing = "Non-Local Means Denoising" # set Denoising as the active setting
            self._collapse_other_groups(self.DenoiseGroup) # set other image processing settings as unchecked / unactivated


    def denoise_values_updated(self):

        self.settings.denoise_Luminance_Strength = self.lumBox.value()
        self.settings.denoise_Color_Strength = self.colBox.value()
        self.settings.denoise_template_size = self.patchBox.value()
        self.settings.denoise_search_window = self.searchBox.value()

# ==========================================================
# High Pass Helpers
# ==========================================================

    def high_pass_toggled(self, checked):
        self.settings.high_pass = checked

        if checked:
            self.settings.active_processing = "High Pass Filter" # set High Pass Filter as the active setting
            self._collapse_other_groups(self.HighPassGroup) # set other image processing settings as unchecked / unactivated

    def high_pass_changed(self):
        self.settings.high_pass_intensity = (
            self.HighPassSlider.value() / 10 # divide by 10 to achieve a range of 6.0 to 12.0, as the slider has a range of 60 to 120 (the slider does not accomodate decimals naturally)
        )
        self.HighPassLabel.setText(
            f"HPF Intensity = {self.HighPassSlider.value()/10:.1f}"
        )

# ==========================================================
# RGB Helpers
# ==========================================================

    def rgb_toggled(self, checked):
        self.settings.rgb = checked

        if checked:
            self.settings.active_processing = "RGB Gain" # set RGB Gain as the active setting
            self._collapse_other_groups(self.RGBGroup) # set other image processing settings as unchecked / unactivated


    def rgb_updates(self):

        sliders = (
            ("red_modifier", self.RedSlider, self.RedLabel, "Red"),
            ("green_modifier", self.GreenSlider, self.GreenLabel, "Green"),
            ("blue_modifier", self.BlueSlider, self.BlueLabel, "Blue"),
        )

        for setting, slider, label, colour in sliders:
            setattr( # update the settings object with the new value for the corresponding color channel, scaling the slider value to a range of 0.0 to 2.0 by dividing by 100
                self.settings,
                setting,
                slider.value() / 100,
            )

            label.setText(
                f"{colour} Intensity = {slider.value()}%"
            )

# ==========================================================
# Threshold
# ==========================================================

    def threshold_toggled(self, checked):
        self.settings.threshold = checked

        if checked:
            self.settings.active_processing = "Thresholding" # set Thresholding as the active setting
            self._collapse_other_groups(self.ThresholdGroup) # set other image processing settings as unchecked / unactivated

            self.update_otsu_label()

    def threshold_update(self):
        self.settings.threshold_value = self.ThresholdValue.value()
        
        mapping = self._button_mapping(self.ThreshChoice) # create a mapping of the thresholding method buttons to their corresponding index values, allowing for easy retrieval of the selected thresholding method when updating the settings object
        selected_button = self.ThreshChoice.checkedButton()

        if mapping[selected_button] == 5: # if Otsu's method is selected, update the label to display the calculated threshold value from the settings object
            self.update_otsu_label()

        # if statement to protect against the case where no button is selected, which would cause an error. 
        # The threshold type is initialized after the threshold value, so this can happen when the threshold value is changed before the threshold type is selected
        if selected_button: 
            self.settings.threshold_type = mapping[selected_button]

    def update_otsu_label(self):
        self.OtsuVal.setText(
            f"Otsu's Method Threshold Value = {self.settings.otsu_value:.2f}"
        )



# ==========================================================
# TXI
# ==========================================================

    def txi_toggled(self, checked):
        self.settings.txi = checked

        if checked:
            self.settings.active_processing = "TXI" # set TXI as the active setting
            self._collapse_other_groups(self.TXIGroup) # set other image processing settings as unchecked / unactivated


    def txi_default(self, checked):
        # Toggle between the user's custom TXI settings and the built-in defaults.

        if checked:
            # Save the user's current values before applying defaults
            self.saved_txi_settings = self._get_txi_values()
            self._set_txi_values(self.DEFAULT_TXI)

        elif self.saved_txi_settings is not None:
            # Restore the user's previous custom values
            self._set_txi_values(self.saved_txi_settings)


    def txi_changed(self):
        # Match the TXI widgets with the processing settings.

        self.settings.txiAlpha = self.TXIAlpha.value()
        self.settings.txiGamma = self.TXIGamma.value()
        self.settings.txiEnhancement = self.TXIEnhancement.value()

        s1, s2 = sorted(( # Maintain the requirement for s1 < s2
            self.txiS1.value(),
            self.txiS2.value(),
        ))

        t1, t2 = sorted(( # Maintain the requirement for t1 < t2
            self.txiT1.value(),
            self.txiT2.value(),
        ))

        # Ensure the lower/upper bounds aren't identical
        if s1 == s2:
            s2 = min(50, s2 + 1)

        if t1 == t2:
            t2 = min(50, t2 + 1)

        # Push any corrected values back into the widgets
        if (s1, s2) != (self.txiS1.value(), self.txiS2.value()):
            self.txiS1.setValue(s1)
            self.txiS2.setValue(s2)

        if (t1, t2) != (self.txiT1.value(), self.txiT2.value()):
            self.txiT1.setValue(t1)
            self.txiT2.setValue(t2)

        self.settings.s1 = s1 # After s1, s2, t1, and t2 have been validated and corrected if necessary, update the settings with the final values
        self.settings.s2 = s2
        self.settings.t1 = t1
        self.settings.t2 = t2


    def _get_txi_values(self):
        # Read the current TXI values from the widgets and return them as a dictionary.

        return {
            "alpha": self.TXIAlpha.value(),
            "gamma": self.TXIGamma.value(),
            "enhancement": self.TXIEnhancement.value(),
            "s1": self.txiS1.value(),
            "s2": self.txiS2.value(),
            "t1": self.txiT1.value(),
            "t2": self.txiT2.value(),
        }


    def _set_txi_values(self, values):
        # Apply a dictionary of TXI values to the widgets.
        # The connected valueChanged signals will automatically update self.settings via txi_changed().

        self.TXIAlpha.setValue(values["alpha"])
        self.TXIGamma.setValue(values["gamma"])
        self.TXIEnhancement.setValue(values["enhancement"])

        self.txiS1.setValue(values["s1"])
        self.txiS2.setValue(values["s2"])
        self.txiT1.setValue(values["t1"])
        self.txiT2.setValue(values["t2"])


class CameraSourceWidget(QWidget):
    FRAME_INTERVAL_MS = 30 # milliseconds between frames, roughly 33 FPS
    BUTTON_SIZE = QSize(200, 100)

    def __init__(self, settings, processing_window):
        super().__init__()

        # Processing
        self.settings = settings
        self.processing_window = processing_window
        self.pipeline = ProcessingPipeline(settings)
        self.processed_image = None

        # Camera
        self.cap = None

        # Camera selection
        camera_choice = QComboBox()
        camera_choice.addItems([
            "No Camera",
            "Camera 0",
            "Camera 1",
            "Camera 2"
        ])
        camera_choice.currentIndexChanged.connect(self.update_camera)

        # Camera Controls
        pause_button = QPushButton("Pause Camera")
        pause_button.setFixedSize(self.BUTTON_SIZE)
        pause_button.setCheckable(True)
        pause_button.toggled.connect(self.pause_camera)

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        # Layouts
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Camera Input:"))
        left_layout.addWidget(camera_choice)
        left_layout.addWidget(pause_button)

        left_layout.addStretch()  # Push the widgets to the top

        layout = QHBoxLayout()
        layout.addLayout(left_layout)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def update_camera(self, index):
        # Switch to the selected camera.

        self.timer.stop()
        self.release_camera()

        if index == 0:
            self.image_label.clear()
            return

        camera_index = index - 1
        self.cap = cv2.VideoCapture(camera_index)

        if not self.cap.isOpened():
            print(f"Could not open camera {camera_index}")
            self.cap = None
            return

        self.timer.start(self.FRAME_INTERVAL_MS)

    def update_frame(self):
        # Capture, process, and display one frame.

        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = self.pipeline.process_image(frame)
        self.processed_image = frame.copy() # store a copy of the processed frame for saving

        qt_image = self.frame_to_qimage(frame)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

        ImageProcessingWindow.update_otsu_label(self.processing_window)

    def frame_to_qimage(self, frame):
        #Convert an OpenCV BGR image to a QImage.

        frame = np.clip(frame, 0, 255).astype(np.uint8)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.ascontiguousarray(frame)

        h, w, ch = frame.shape # get the height, width, and number of channels of the frame
        bytes_per_line = ch * w # calculate the number of bytes per line (row) of the image

        return QImage( # Convert the processed frame to a QImage for display 
            frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888 # specify the format of the image data as RGB with 8 bits per channel
        )

    def pause_camera(self, checked):
        # Pause or resume frame updates.

        if checked:
            self.timer.stop()
        elif self.cap is not None and self.cap.isOpened():
            self.timer.start(self.FRAME_INTERVAL_MS)

    def release_camera(self):
        # Release the current camera if one is open.

        if self.cap is not None:
            if self.cap.isOpened():
                self.cap.release()
            self.cap = None

    def closeEvent(self, event):
        # Clean up resources when the widget closes.

        self.timer.stop()
        self.release_camera()
        super().closeEvent(event)


class FolderSourceWidget(QWidget):
    BUTTON_SIZE = QSize(200, 100)
    AUTO_ADVANCE_INTERVAL = 2000 # milliseconds between automatic image advances, set to 2 seconds
    REFRESH_INTERVAL = 200 # milliseconds between refreshes of the displayed image, set to 0.2 seconds

    def __init__(self, settings, processing_window):
        super().__init__()

        # Processing
        self.settings = settings
        self.processing_window = processing_window
        self.pipeline = ProcessingPipeline(settings)
        self.processed_image = None

        # Layouts
        main_layout = QHBoxLayout()
        controls_layout = QVBoxLayout()

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Image selection
        self.combo = QComboBox()

        self.image_files = sorted(Path("kvasir-ulcerative-colitis").glob("*.jpg"))
        for file in self.image_files:
            self.combo.addItem(file.stem)

        controls_layout.addWidget(self.combo)

        # Navigation buttons
        next_button = QPushButton("Next Image")
        next_button.setFixedSize(self.BUTTON_SIZE)

        previous_button = QPushButton("Previous Image")
        previous_button.setFixedSize(self.BUTTON_SIZE)

        controls_layout.addWidget(next_button)
        controls_layout.addWidget(previous_button)

        # Auto advance
        auto_advance_button = QPushButton("Automatically\nAdvance Image")
        auto_advance_button.setFixedSize(self.BUTTON_SIZE)
        auto_advance_button.setCheckable(True)

        self.auto_advance_timer = QTimer(self)
        self.auto_advance_timer.setInterval(self.AUTO_ADVANCE_INTERVAL)
        self.auto_advance_timer.timeout.connect(self.next_image)

        controls_layout.addWidget(auto_advance_button)

        # Keep controls aligned at the top
        controls_layout.addStretch()

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)

        # Assemble layout
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.image_label)

        self.setLayout(main_layout)

        # Load initial image
        if self.image_files:
            self.combo.setCurrentIndex(0)
            self.update_image(0)

        # Signal connections
        self.combo.currentIndexChanged.connect(self.update_image)
        next_button.clicked.connect(self.next_image)
        previous_button.clicked.connect(self.previous_image)
        auto_advance_button.toggled.connect(self.toggle_auto_advance)

        # Refresh timer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(
            lambda: self.update_image(self.combo.currentIndex())
        )
        self.refresh_timer.start(self.REFRESH_INTERVAL)

    def toggle_auto_advance(self, checked):
        if checked:
            self.auto_advance_timer.start()
        else:
            self.auto_advance_timer.stop()

    def next_image(self):
        current = self.combo.currentIndex()
        next_index = (current + 1) % self.combo.count()
        self.combo.setCurrentIndex(next_index)

    def previous_image(self):
        current = self.combo.currentIndex()
        previous_index = (current - 1) % self.combo.count()
        self.combo.setCurrentIndex(previous_index)

    def update_image(self, index):
        if not self.image_files:
            return

        path = self.image_files[index]

        frame = cv2.imread(str(path))
        frame = self.pipeline.process_image(frame)
        self.processed_image = frame.copy() # store a copy of the processed frame for saving

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)

        h, w, ch = rgb.shape # get the height, width, and number of channels of the processed image
        qimg = QImage( # convert the processed image to a QImage for display
            rgb.data, 
            w,
            h,
            ch * w, # calculate the number of bytes per line (row) of the image
            QImage.Format_RGB888 # specify the format of the image data as RGB with 8 bits per channel
        )

        self.image_label.setPixmap(QPixmap.fromImage(qimg))

        ImageProcessingWindow.update_otsu_label(self.processing_window) # update the Otsu's method threshold value label in the processing settings window

    def refresh_image(self):
        if self.image_files:
            self.update_image(self.combo.currentIndex())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_image()

        
class MainWindow(QMainWindow):

    def __init__(self, app):
        super().__init__()

        # Application
        self.app = app
        self.setWindowTitle("Radek MSc - Image Processing Program")

        # Processing
        self.settings = ImageProcessingSettings()
        self.processing_window = ImageProcessingWindow(self.settings)
        self.processing_window.setWindowFlags( # set the window flags for the processing window to make it a tool window that stays on top of other windows
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Theme
        with open("Toolery_LightMode.qss", "r") as file:
            self.app.setStyleSheet(file.read())

        # Layouts
        main_layout = QHBoxLayout()
        sidebar_layout = QVBoxLayout()
        save_layout = QVBoxLayout() 

        main_layout.setContentsMargins(0, 0, 0, 0)
        save_layout.setContentsMargins(15, 0, 15, 0)

        # Toolbar
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))

        processing_action = QAction(
            QIcon("gear.png"),
            "&Image Processing Settings",
            self
        )
        processing_action.setStatusTip("Open the image processing settings.")
        processing_action.setCheckable(True)
        processing_action.triggered.connect(
            self.toggle_processing_window
        )
        toolbar.addAction(processing_action)
        toolbar.addSeparator()

        dark_mode_action = QAction(
            QIcon("DarkMode.png"),
            "&Dark Mode",
            self
        )
        dark_mode_action.setStatusTip("Toggle dark mode.")
        dark_mode_action.setCheckable(True)
        dark_mode_action.triggered.connect(
            self.toggle_dark_mode
        )
        toolbar.addAction(dark_mode_action)

        save_action = QAction(
            QIcon("save.png"),
            "&Save Image",
            self
        )
        save_action.setStatusTip("Save the current processed image.")
        save_action.triggered.connect(self.save_image)
        toolbar.addAction(save_action)

        # Image source selection
        source_list = QListWidget()
        source_list.addItems([
            "KVASIR Image Folder",
            "Camera"
        ])
        source_list.setFixedWidth(200)

        sidebar_layout.addWidget(source_list)
        sidebar_layout.addStretch()

        # Save controls
        self.save_image_button = QPushButton("Save Image")
        self.save_image_button.clicked.connect(self.save_image)
        save_layout.addWidget(self.save_image_button)

        self.save_with_metadata = QCheckBox(
            "Include Processing\nMetadata"
        )
        self.save_with_metadata.setChecked(True)
        save_layout.addWidget(self.save_with_metadata)
        save_layout.addStretch()

        # Image source widgets
        self.stack = QStackedWidget()

        self.folder_widget = FolderSourceWidget(
            self.settings,
            self.processing_window
        )        
        self.camera_widget = CameraSourceWidget(
            self.settings,
            self.processing_window
        )

        self.stack.addWidget(self.folder_widget)
        self.stack.addWidget(self.camera_widget)
        self.stack.setCurrentIndex(0)

        # Layout assembly
        source_list.currentRowChanged.connect(
            self.stack.setCurrentIndex
        )

        sidebar_layout.addLayout(save_layout)
        main_layout.addLayout(sidebar_layout)
        main_layout.addWidget(self.stack)

        container = QWidget()
        container.setLayout(main_layout)

        self.setCentralWidget(container)
    
    def save_image(self):
        # Save the currently displayed processed image.

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "PNG (*.png);;JPEG (*.jpg)"
        )

        if not filename:
            return

        image = self.stack.currentWidget().processed_image

        if image is None:
            QMessageBox.warning(
                self,
                "No Image",
                "There is no processed image to save."
            )
            return

        cv2.imwrite(filename, image)

        if self.save_with_metadata.isChecked():
            metadata = self.settings.to_metadata()
            self.write_metadata(filename, metadata)


    def write_metadata(self, filename, metadata):
        # Embed processing metadata into a saved PNG image.

        image = Image.open(filename)

        pnginfo = PngInfo()
        pnginfo.add_text(
            "Radek MSc",
            json.dumps(metadata, indent=4)
        )

        image.save(filename, pnginfo=pnginfo)


    def toggle_processing_window(self, checked):
        # Show or hide the image processing settings window.

        if self.processing_window.isVisible():
            self.processing_window.hide()
        else:
            self.processing_window.show()
            self.processing_window.raise_()
            self.processing_window.activateWindow()


    def toggle_dark_mode(self, checked):
        # Switch between the light and dark application themes.

        stylesheet = (
            "Toolery_DarkMode.qss"
            if checked
            else "Toolery_LightMode.qss"
        )

        with open(stylesheet, "r") as file:
            self.app.setStyleSheet(file.read())

        self.app.processEvents()