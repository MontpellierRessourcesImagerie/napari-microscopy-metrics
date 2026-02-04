"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""

from typing import TYPE_CHECKING, Optional
import types
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QLabel, QSlider, QVBoxLayout, QToolBox, QRadioButton, QButtonGroup, QComboBox, QStackedWidget, QSizePolicy, QDialog
from skimage.util import img_as_float
from microscopy_metrics.detection import *
import napari

class ParamsSignal(QObject):
    params_updated = Signal(dict)

class Detection_Parameters_Widget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer", params):
        super().__init__()
        self.viewer = viewer
        self.params = params
        self.signal = ParamsSignal()
        self.compteur = 0

        layout = QVBoxLayout()

        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.counter_label = QLabel(f"Nombre de clics : {self.compteur}")
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.btn = QPushButton("Cliquez ici !")
        self.btn.clicked.connect(self.increment_counter) 
        layout.addWidget(self.counter_label)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def increment_counter(self):
        """Incrémente le compteur et met à jour l'affichage."""
        self.compteur += 1
        self.counter_label.setText(f"Nombre de clics : {self.compteur}")
        self.params = {"compteur" : self.compteur}
        self.signal.params_updated.emit(self.params)



class Microscopy_Metrics_QWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.params = {}

        self.filtered_layer = None
        
        self.detection_Label = QLabel()
        self.detection_Label.setText("PSF detection tool")

        self.detection_tool_selection = QComboBox()
        L = ["peak_local_max", "blob_log","blob_dog"]
        self.detection_tool_selection.addItems(L)
        self.detection_tool_selection.currentIndexChanged.connect(self._selected_action)
        
        # ToolBox for selecting the detection method
        self.params_stack = QStackedWidget()
        
        # Widget for the peak_local_max method
        self.peak_method_widget = QWidget()
        self.peak_method_layout = QVBoxLayout()
        self.peak_method_layout.setContentsMargins(0,0,0,0)
        self.peak_method_layout.setSpacing(2)
        # Slider for the minimal distance between two PSF
        self.min_distance_detection = QSlider(Qt.Horizontal)
        self.min_distance_detection.setRange(0,20)
        self.min_distance_detection.setValue(10)
        self.min_distance_detection.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.min_distance_label = QLabel("Minimal distance :" + str(self.min_distance_detection.value()))
        self.min_distance_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.peak_method_layout.addWidget(self.min_distance_label)
        self.peak_method_layout.addWidget(self.min_distance_detection)
        self.peak_method_widget.setLayout(self.peak_method_layout)

        # Widget for the blobs method
        self.centroid_method_widget = QWidget()
        self.centroid_method_layout = QVBoxLayout()
        self.centroid_sigma_slider = QSlider(Qt.Horizontal)
        self.centroid_sigma_slider.setRange(1,10)
        self.centroid_sigma_slider.setValue(3)
        self.centroid_sigma_label = QLabel("Sigma : " + str(self.centroid_sigma_slider.value()))
        self.centroid_method_layout.addWidget(self.centroid_sigma_label)
        self.centroid_method_layout.addWidget(self.centroid_sigma_slider)
        self.centroid_method_widget.setLayout(self.centroid_method_layout)

        self.params_stack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.params_stack.addWidget(self.peak_method_widget)
        self.params_stack.addWidget(self.centroid_method_widget)

        # Slider for the relative threshold
        self.threshold_rel = QSlider(Qt.Horizontal)
        self.threshold_rel.setRange(0,100)
        self.threshold_rel.setValue(50)
        self.threshold_rel_label = QLabel("Relative threshold : " + str(self.threshold_rel.value()/100))

        self.detection_btn = QPushButton("Process")
        self.detection_btn.clicked.connect(self._open_parameters_window)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.detection_Label)
        self.layout().addWidget(self.detection_tool_selection)
        self.layout().addWidget(self.params_stack)
        self.layout().addWidget(self.threshold_rel_label)
        self.layout().addWidget(self.threshold_rel)
        self.layout().addWidget(self.detection_btn)

        self.min_distance_detection.valueChanged.connect(self._update_min_distance_label)
        self.centroid_sigma_slider.valueChanged.connect(lambda value: self.centroid_sigma_label.setText("Sigma : " + str(value)))
        self.threshold_rel.valueChanged.connect(self._update_threshold_label)

    def _selected_action(self, index):
        if index ==2 :
            index = 1
        self.params_stack.setCurrentIndex(index)

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
        if self.detection_tool_selection.currentIndex() == 0 :
            print("Processing peak_local_max psf detection...")
            min_distance = self.min_distance_detection.value()
            filtered_beads = detect_psf_peak_local_max(image, min_distance, threshold)
        elif self.detection_tool_selection.currentIndex() == 1:
            print("Processing blob_log psf detection...")
            sigma = self.centroid_sigma_slider.value()
            filtered_beads = detect_psf_blob_log(image, sigma, threshold)
        else : 
            print("Processing blob_dog psf detection...")
            sigma = self.centroid_sigma_slider.value()
            filtered_beads = detect_psf_blob_dog(image, sigma, threshold)
        if isinstance(filtered_beads, np.ndarray) and filtered_beads.size > 0 :
            if self.filtered_layer is None :
                self.filtered_layer = self.viewer.add_points(filtered_beads,name="PSF detected", face_color='red', opacity=0.5)
            else : 
                self.filtered_layer.data = filtered_beads
        else :
            print("No PSF found or incorrect format.")

    def _open_parameters_window(self):
        self.parameters_window = QDialog(self)
        self.parameters_window.setWindowTitle("Detection parameters")
        self.parameters_window.setModal(True)
        parameters_widget = Detection_Parameters_Widget(self.viewer, self.params)
        parameters_widget.signal.params_updated.connect(self.on_params_updated)
        parameters_layout = QVBoxLayout()
        parameters_layout.addWidget(parameters_widget)
        self.parameters_window.setLayout(parameters_layout)
        self.parameters_window.show()
    
    def on_params_updated(self, new_params):
        self.params = new_params
        print(f"Paramètres mis à jour : {self.params}")