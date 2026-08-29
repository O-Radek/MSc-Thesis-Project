# MSc-Thesis-Project
Final Project for master's degree: Creating a GUI for image processing, with a key application being endoscopy imaging. 

Update 1 (June 5, 2026): Files for this week's work have been uploaded. A basic GUI has been created with room to modify and change. 
Only the Kvasir image folder was not uploaded, due to its size. The image folder can be found here: https://datasets.simula.no/kvasir/
Specifically, the kvasir-v1 zip file and the kvasir-ulcerative-colitis folder. 

Update 2 (June 23, 2026): The organization of the code has been modified, requiring 4 Python files to run. These are: MAIN, GUI_WORK, SETTINGS, and PROJECT. MAIN is where the app is run from, GUI Work handles the GUI and connects users to the Image Processing. PROJECT handles the image processing. SETTINGS is a separate file containing all the options users can modify for their image processing work. Additionally, this update contains a new image processing method: CLAHE (Contrast Limited Adaptive Histogram Equalization), with users able to modify the clip limit, tile grid size, and, if they are using CLAHE with LAB (Lightness, Green/Red Axis, Blue/Yellow axis) or HSV (Hue, Saturation, Value). 

Final Update (August 29, 2026): Final Update (August 29, 2026): All code and image updates have been uploaded with the exception of the PROJECT.py file responsible for the image processing functions for this project. This file contains an interpretation of the TXI algorithm used by Olympus, as described in Tomoya Sato's research paper. Due to not wanting to infringe on any copyright laws, this implementation is kept outside of any public domain.  
