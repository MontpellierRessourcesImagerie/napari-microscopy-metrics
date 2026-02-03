"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""

from typing import TYPE_CHECKING, Optional

from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QLabel, QSlider, QVBoxLayout, QToolBox, QRadioButton, QButtonGroup
from skimage.util import img_as_float
from microscopy_metrics.detection import *
import napari

class Microscopy_Metrics_QWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.compteur = 10
        self.filtered_layer = None
        self.filter_layer = None
        
        self.detection_Label = QLabel()
        self.detection_Label.setText("PSF detection tool")
        
        # ToolBox for selecting the detection method
        self.detection_selector = QToolBox()
        
        # Widget for the peak_local_max method
        self.peak_method_widget = QWidget()
        self.peak_method_layout = QVBoxLayout()
        self.peak_method_radio = QRadioButton("Peak local max method")
        # Slider for the minimal distance between two PSF
        self.min_distance_detection = QSlider(Qt.Horizontal)
        self.min_distance_detection.setRange(0,20)
        self.min_distance_detection.setValue(10)
        self.min_distance_label = QLabel("Minimal distance :" + str(self.min_distance_detection.value()))
        self.peak_method_layout.addWidget(self.peak_method_radio)
        self.peak_method_layout.addWidget(self.min_distance_label)
        self.peak_method_layout.addWidget(self.min_distance_detection)
        self.peak_method_widget.setLayout(self.peak_method_layout)

        # Widget for the Centroid method
        self.centroid_method_widget = QWidget()
        self.centroid_method_layout = QVBoxLayout()
        self.centroid_method_radio = QRadioButton("Centroid method")
        self.centroid_sigma_slider = QSlider(Qt.Horizontal)
        self.centroid_sigma_slider.setRange(1,10)
        self.centroid_sigma_slider.setValue(3)
        self.centroid_sigma_label = QLabel("Sigma : " + str(self.centroid_sigma_slider.value()))
        self.centroid_method_layout.addWidget(self.centroid_method_radio)
        self.centroid_method_layout.addWidget(self.centroid_sigma_label)
        self.centroid_method_layout.addWidget(self.centroid_sigma_slider)
        self.centroid_method_widget.setLayout(self.centroid_method_layout)

        self.detection_selector.addItem(self.peak_method_widget, "Peak local max method")
        self.detection_selector.addItem(self.centroid_method_widget, "Centroids method")

        # Slider for the relative threshold
        self.threshold_rel = QSlider(Qt.Horizontal)
        self.threshold_rel.setRange(0,100)
        self.threshold_rel.setValue(50)
        self.threshold_rel_label = QLabel("Relative threshold : " + str(self.threshold_rel.value()/100))

        self.detection_btn = QPushButton("Process")
        self.detection_btn.clicked.connect(self._on_detect_psf)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.detection_Label)
        self.layout().addWidget(self.detection_selector)
        self.layout().addWidget(self.threshold_rel_label)
        self.layout().addWidget(self.threshold_rel)
        self.layout().addWidget(self.detection_btn)

        self.min_distance_detection.valueChanged.connect(self._update_min_distance_label)
        self.centroid_sigma_slider.valueChanged.connect(lambda value: self.centroid_sigma_label.setText("Sigma : " + str(value)))
        self.threshold_rel.valueChanged.connect(self._update_threshold_label)

    def _update_min_distance_label(self,value):
        self.min_distance_label.setText("Minimal distance :" + str(value))
    
    def _update_threshold_label(self, value):
        self.threshold_rel_label.setText("Relative threshold : " + str(value/100))

    def _on_detect_psf(self):
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image) :
            print("Please, select a valid layer of type Image")
            return 

        image = current_layer.data
        threshold = self.threshold_rel.value()/100

        if self.peak_method_radio.isChecked():
            min_distance = self.min_distance_detection.value()
            filtered_beads = detect_psf_positions(image, min_distance, threshold)
        else :
            sigma = self.centroid_sigma_slider.value()
            filtered_beads = detect_psf_centroids(image, sigma, threshold)
        
        if isinstance(filtered_beads, np.ndarray) and filtered_beads.size > 0 :
            if self.filtered_layer is None :
                #self.filter_layer = self.viewer.add_image(filtered_image, name="Filtered image")
                self.filtered_layer = self.viewer.add_points(filtered_beads,name="PSF detected", face_color='red', opacity=0.5)
            else : 
                self.filtered_layer.data = filtered_beads
                #self.filter_layer.data = filtered_image
        else :
            print("No PSF found or incorrect format.")