class ImageProcessingSettings:
    def __init__(self):
        self.high_pass = False

        self.clahe = False
        self.clahe_clip = 1
        self.clahe_tile = 4
        self.clahe_lab = True