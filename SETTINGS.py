class ImageProcessingSettings:
    def __init__(self):
        self.active_processing = None

        self.clahe = False
        self.clahe_clip = 1
        self.clahe_tile = 4
        self.clahe_lab = True # True = LAB, False = HSV

        self.denoise = False
        self.denoise_Luminance_Strength = 10
        self.denoise_Color_Strength = 10
        self.denoise_template_size = 7
        self.denoise_search_window = 15

        self.high_pass = False
        self.high_pass_intensity = 8.0
        
        self.rgb = False
        self.red_modifier = 1
        self.green_modifier = 1
        self.blue_modifier = 1

        self.threshold = False
        self.threshold_type = 0
        self.threshold_value = 127
        self.otsu_value = 0

        self.txi = False
        self.txiDefault = True # binary to use / don't use the values originally chosen
        self.txiAlpha = 1.4 # the denominator. TXI originally uses 1 / 1.4 as the alpha value
        self.txiGamma = 2.2
        self.txiEnhancement = 1.2 # enhancement parameter (g in TXI paper)
        self.s1 = 15 # "range between s1 and s2 represents expansion target range"
        self.s2 = 30 # "enhancement range between t1 and t2 make it possible to enhance the color contrast"
        self.t1 = 5
        self.t2 = 30

    def to_metadata(self):
        return {
            "software": "Radek MSc Thesis",
            "version": "1.0",
            "active_processing": self.active_processing,
            "processing": {
                "clahe": {
                    "enabled": self.clahe,
                    "clip_limit": self.clahe_clip,
                    "tile_size": self.clahe_tile,
                    "lab": self.clahe_lab,
                },
                "denoise": {
                    "enabled": self.denoise,
                    "luminance_strength": self.denoise_Luminance_Strength,
                    "color_strength": self.denoise_Color_Strength,
                    "template_size": self.denoise_template_size,
                    "search_window": self.denoise_search_window,
                },

                "high_pass": {
                    "enabled": self.high_pass,
                    "intensity": self.high_pass_intensity,
                },

                "rgb": {
                    "enabled": self.rgb,
                    "red": self.red_modifier,
                    "green": self.green_modifier,
                    "blue": self.blue_modifier,
                },
                "threshold": {
                    "enabled": self.threshold,
                    "type": self.threshold_type,
                    "value": self.threshold_value,
                },
                
                "txi": {
                    "enabled": self.txi,
                    "default": self.txiDefault,
                    "alpha": self.txiAlpha,
                    "gamma": self.txiGamma,
                    "enhancement": self.txiEnhancement,
                    "s1": self.s1,
                    "s2": self.s2,
                    "t1": self.t1,
                    "t2": self.t2,
                },
            }
        }
