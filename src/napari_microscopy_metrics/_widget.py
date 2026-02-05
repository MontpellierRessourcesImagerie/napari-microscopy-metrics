"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""

from typing import TYPE_CHECKING, Optional
import types
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget, QLabel, QSlider, QVBoxLayout, QToolBox, QRadioButton, QButtonGroup, QComboBox, QStackedWidget, QSizePolicy, QDialog, QCheckBox
from skimage.util import img_as_float
from microscopy_metrics.detection import *
import napari
from .json_utils import *

class ParamsSignal(QObject):
    params_updated = Signal(dict)

class Detection_Parameters_Widget(QWidget):
    def __init__(self, viewer: "napari.viewer.Viewer", params):
        super().__init__()
        self.viewer = viewer
        self.params = params
        self.signal = ParamsSignal()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.btn = QPushButton("Confirm")
        self.btn.clicked.connect(self._on_confirm) 

        layout.addWidget(self.counter_label)
        layout.addWidget(self.btn)
        self.setLayout(layout)

    def _on_confirm(self):
        """Send parameters to main window and close this one."""
        self.signal.params_updated.emit(self.params)



class Microscopy_Metrics_QWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.params = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
        }

        loaded_params = read_file_data("parameters_data.json")
        if loaded_params:
            self.params.update(loaded_params)

        self.filtered_layer = None
        self.filter_layer = None
        
        self.detection_Label = QLabel()
        self.detection_Label.setText("PSF detection tool")

        self.detection_tool_selection = QComboBox()
        L = ["peak_local_max", "blob_log","blob_dog","centroid"]
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
        self.min_distance_detection.setValue(self.params["Min_dist"])
        self.min_distance_detection.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.min_distance_label = QLabel("Minimal distance :" + str(self.min_distance_detection.value()))
        self.min_distance_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.peak_method_layout.addWidget(self.min_distance_label)
        self.peak_method_layout.addWidget(self.min_distance_detection)
        self.peak_method_widget.setLayout(self.peak_method_layout)

        # Widget for the blobs method
        self.blob_method_widget = QWidget()
        self.blob_method_layout = QVBoxLayout()
        self.blob_sigma_slider = QSlider(Qt.Horizontal)
        self.blob_sigma_slider.setRange(1,10)
        self.blob_sigma_slider.setValue(self.params["Sigma"])
        self.blob_sigma_label = QLabel("Sigma : " + str(self.blob_sigma_slider.value()))
        self.blob_method_layout.addWidget(self.blob_sigma_label)
        self.blob_method_layout.addWidget(self.blob_sigma_slider)
        self.blob_method_widget.setLayout(self.blob_method_layout)

        # Widget for the centroid method
        self.centroid_method_widget = QWidget()
        self.centroid_method_layout = QVBoxLayout()
        self.centroid_method_widget.setLayout(self.centroid_method_layout)

        self.params_stack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.params_stack.addWidget(self.peak_method_widget)
        self.params_stack.addWidget(self.blob_method_widget)
        self.params_stack.addWidget(self.centroid_method_widget)

        # Slider for the relative threshold
        self.threshold_rel = QSlider(Qt.Horizontal)
        self.threshold_rel.setRange(0,100)
        self.threshold_rel.setValue(self.params["Rel_threshold"])
        self.threshold_rel_label = QLabel("Relative threshold : " + str(self.threshold_rel.value()/100))

        self.threshold_auto_check = QCheckBox()
        self.threshold_auto_check.setChecked(False)
        #self.parameters_btn = QPushButton("Parameters")
        #self.parameters_btn.clicked.connect(self._open_parameters_window)
        self.detection_btn = QPushButton("Process")
        self.detection_btn.clicked.connect(self._on_detect_psf)

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.detection_Label)
        self.layout().addWidget(self.detection_tool_selection)
        self.layout().addWidget(self.params_stack)
        self.layout().addWidget(self.threshold_rel_label)
        self.layout().addWidget(self.threshold_rel)
        self.layout().addWidget(QLabel("Apply an automatic threshold ?"))
        self.layout().addWidget(self.threshold_auto_check)
        #self.layout().addWidget(self.parameters_btn)
        self.layout().addWidget(self.detection_btn)


        self.min_distance_detection.valueChanged.connect(self._update_min_distance)
        self.blob_sigma_slider.valueChanged.connect(self._update_sigma)
        self.threshold_rel.valueChanged.connect(self._update_threshold)
        self.viewer.layers.events.removed.connect(self._on_layer_removed)


    def _selected_action(self, index):
        if index >=2 :
            index = index - 1
        self.params_stack.setCurrentIndex(index)

    def _update_min_distance(self,value):
        self.min_distance_label.setText("Minimal distance :" + str(value))
        self.params["Min_dist"] = value
    
    def _update_sigma(self,value):
        self.blob_sigma_label.setText("Sigma : " + str(value))
        self.params["Sigma"] = value
    
    def _update_threshold(self, value):
        self.threshold_rel_label.setText("Relative threshold : " + str(value/100))
        self.params["Rel_threshold"] = value

    def _on_layer_removed(self,event):
        if hasattr(self,'filtered_layer') and self.filtered_layer == event.value:
            self.filtered_layer = None
        if hasattr(self,'filter_layer') and self.filter_layer == event.value:
            self.filter_layer = None

    def _on_detect_psf(self):
        write_file_data("parameters_data.json", self.params)
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image) :
            print("Please, select a valid layer of type Image")
            return 
        image = current_layer.data
        threshold = self.params["Rel_threshold"]/100
        auto_threshold = self.threshold_auto_check.isChecked()
        binary_image = None
        if self.detection_tool_selection.currentIndex() == 0 :
            print("Processing peak_local_max psf detection...")
            min_distance = self.params["Min_dist"]
            filtered_beads = detect_psf_peak_local_max(image, min_distance, threshold,auto_threshold)
        elif self.detection_tool_selection.currentIndex() == 1:
            print("Processing blob_log psf detection...")
            sigma = self.params["Sigma"]
            filtered_beads = detect_psf_blob_log(image, sigma, threshold,auto_threshold)
        elif self.detection_tool_selection.currentIndex() == 2 : 
            print("Processing blob_dog psf detection...")
            sigma = self.params["Sigma"]
            filtered_beads = detect_psf_blob_dog(image, sigma, threshold,auto_threshold)
        else :
            print("Processing centroid psf detection...")
            filtered_beads,binary_image = detect_psf_centroid(image,threshold, auto_threshold)
        if isinstance(filtered_beads, np.ndarray) and filtered_beads.size > 0 :
            rois = extract_Region_Of_Interest(filtered_beads)
            if self.filter_layer is None :
                self.filter_layer = self.viewer.add_shapes(rois,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
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
        self.parameters_window.close()