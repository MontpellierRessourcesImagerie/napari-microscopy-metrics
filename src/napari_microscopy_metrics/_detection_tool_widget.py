"""
This module contains a napari widgets for PSF detection
"""
from pathlib import Path
from typing import TYPE_CHECKING, Optional
import types
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject
from qtpy.QtWidgets import *
from qtpy.QtGui import QIntValidator, QIcon
from skimage.util import img_as_float
from microscopy_metrics.detection import *
from microscopy_metrics.metrics import * 
import napari
from napari.settings import get_settings
from napari.utils.notifications import *
from .json_utils import *
from autooptions import *


class ParamsSignal(QObject):
    """ Class for the declaration of update parameters signal"""
    params_updated = Signal(dict)

class Detection_Parameters_Widget(QWidget):
    """ Widget for processing PSF detection and extraction
    
    Parameters
    ----------
    viewer : napari.viewer.Viewer
        The napari viewer were the widget will be displayed
    params : dict  
        The dataset concerning parameters for the detection and extraction.
    """
    def __init__(self, viewer: "napari.viewer.Viewer", params):
        super().__init__()
        self.viewer = viewer
        self.params = params
        self.signal = ParamsSignal()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.detection_Label = QLabel()
        self.detection_Label.setText("PSF detection tool parameters")
        self.detection_tool_selection = QComboBox()
        L = ["peak_local_max", "blob_log","blob_dog","centroid"]
        self.detection_tool_selection.addItems(L)
        self.detection_tool_selection.setCurrentIndex(self.params["selected_tool"])
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

        # Button for the automatic threshold calculation
        self.threshold_auto_check = QCheckBox()
        self.threshold_auto_check.setChecked(self.params["auto_threshold"])

        # Option for the choice of the threshold
        self.options_threshold = Options("Threshold choice", "Median Filter")
        self.options_threshold.addChoice(name="choose a threshold", value=str(self.params["threshold_choice"]), choices=["otsu", "isodata", "li", "minimum", "triangle"])
        self.widget_threshold = OptionsWidget(self.viewer,self.options_threshold)

        # Options for the ROI
        self.options_ROI = Options("ROI specifications","Median Filter")
        self.options_ROI.addFloat(name="Theoretical bead size (µm)", value=self.params["theorical_bead_size"])
        self.widget_ROI = OptionsWidget(self.viewer,self.options_ROI)
        
        # Slider for the crop factor of ROI
        self.crop_factor = QSlider(Qt.Horizontal)
        self.crop_factor.setRange(1,10)
        self.crop_factor.setValue(self.params["crop_factor"])
        self.crop_factor_label = QLabel("Crop factor : " + str(self.crop_factor.value()))

        # Options for rejection zone and annulus definition
        self.options_rejection = Options("Rejection specifications","Median Filter")
        self.options_rejection.addFloat(name="Z axis rejection margin (µm)", value=self.params["rejection_zone"])
        self.options_rejection.addFloat(name="Inner annulus distance to bead (µm)", value=self.params["distance_annulus"])
        self.options_rejection.addFloat(name="Annulus thickness (µm)", value=self.params["thickness_annulus"])
        self.widget_rejection = OptionsWidget(self.viewer,self.options_rejection)
        self.widget_rejection.addApplyButton(self._on_confirm)
        # Adding all the widgets to the layout
        layout.addWidget(self.detection_Label)
        layout.addWidget(self.detection_tool_selection)
        layout.addWidget(self.params_stack)
        layout.addWidget(self.threshold_rel_label)
        layout.addWidget(self.threshold_rel)
        layout.addWidget(QLabel("Apply an automatic threshold ?"))
        layout.addWidget(self.threshold_auto_check)
        layout.addWidget(self.widget_threshold)
        layout.addWidget(self.widget_ROI)
        layout.addWidget(self.crop_factor_label)
        layout.addWidget(self.crop_factor)
        layout.addWidget(self.widget_rejection)

        # Defining the layout of the widget
        self.setLayout(layout)

        # Linking signals to slots
        self.min_distance_detection.valueChanged.connect(self._update_min_distance)
        self.blob_sigma_slider.valueChanged.connect(self._update_sigma)
        self.threshold_rel.valueChanged.connect(self._update_threshold)
        self.crop_factor.valueChanged.connect(self._update_crop_factor)
        self.threshold_auto_check.stateChanged.connect(self._update_auto_threshold)
        # Initial calls for updating states at launch
        self._selected_action(self.detection_tool_selection.currentIndex())
    
    # Defining slots
    def _on_confirm(self):
        """Send parameters to main window and close this one"""
        self.update_params()
        self.signal.params_updated.emit(self.params)

    def _update_min_distance(self,value):
        """Update the label for minimal distance and assign the value in params"""
        self.min_distance_label.setText("Minimal distance :" + str(value))
        self.params["Min_dist"] = value
    
    def _update_sigma(self,value):
        """Update the label for sigma and assign the value in params """
        self.blob_sigma_label.setText("Sigma : " + str(value))
        self.params["Sigma"] = value
    
    def _update_threshold(self, value):
        """Update the label for relative threshold and assign the value in params"""
        self.threshold_rel_label.setText("Relative threshold : " + str(value/100))
        self.params["Rel_threshold"] = value

    def _update_crop_factor(self, value):
        """Updates the label for crop factor and assign the value in params"""
        self.crop_factor_label.setText("Crop factor : " + str(value))
        self.params["crop_factor"] = value

    def _selected_action(self, index):
        """Update the display for selected tool and assign the value in params"""
        self.params["selected_tool"] = index
        if index >=2 :
            index = index - 1
        self.params_stack.setCurrentIndex(index)
    
    def _update_auto_threshold(self,value):
        """Assign the value in params"""
        self.params["auto_threshold"] = value == 2
    
    def update_params(self):
        """Function to update user preferencies"""
        self.widget_rejection.transferValues()
        self.widget_ROI.transferValues()
        self.widget_threshold.transferValues()
        self.params["theorical_bead_size"] = self.options_ROI.value("Theoretical bead size (µm)")
        self.params["rejection_zone"] = self.options_rejection.value("Z axis rejection margin (µm)")
        self.params["distance_annulus"] = self.options_rejection.value("Inner annulus distance to bead (µm)")
        self.params["thickness_annulus"] = self.options_rejection.value("Annulus thickness (µm)")
        self.params["threshold_choice"] = self.options_threshold.value("choose a threshold")


class Detection_Tool_Tab(QWidget):
    """ The main widget of the detection tool
    
    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.count_windows = 0
        self.params = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
            "theorical_bead_size":10,
            "crop_factor":5,
            "selected_tool":0,
            "auto_threshold":False,
            "rejection_zone":10,
            "distance_annulus" : 10,
            "thickness_annulus": 10,
            "threshold_choice":"otsu"
        }
        #Read and restore datas if exist
        loaded_params = read_file_data("parameters_data.json")
        if loaded_params:
            self.params.update(loaded_params)

        #Layers for displaying centroids (point) and region of interest (shapes)
        self.filtered_layer = None
        self.filter_layer = None
        self.filtered_beads = None
        self.rois = None
        self.cropped_layers = []

        # Button to access parameters
        self.parameters_btn = QPushButton()
        self.parameters_btn.clicked.connect(self._open_parameters_window)
        icon_path = self.get_logo_path(get_settings().appearance.theme)
        self.parameters_btn.setIcon(QIcon(str(icon_path)))
        self.parameters_btn.setIconSize(QSize(35,35))
        self.parameters_btn.setFixedSize(35, 35)
        
        # Button to process beads detection
        self.detection_btn = QPushButton("Visualize beads detection")
        self.detection_btn.clicked.connect(self._on_detect_psf)

        # Affichage des résultats
        self.results_label = QLabel()

        # Adding all the widgets to the layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.parameters_btn)
        layout.addWidget(self.detection_btn)
        layout.addWidget(self.results_label)
        layout.addStretch()
        self.setLayout(layout)

        # Linking signals to slots
        self.viewer.layers.events.removed.connect(self._on_layer_removed)
    # Defining slots
    def _on_layer_removed(self,event):
        """Manage the suppression of ROI and centroids layers"""
        if hasattr(self,'filtered_layer') and self.filtered_layer == event.value:
            self.filtered_layer = None
        if hasattr(self,'filter_layer') and self.filter_layer == event.value:
            self.filter_layer = None
        if hasattr(self, 'cropped_layers') and event.value in self.cropped_layers:
            self.cropped_layers.remove(event.value)


    def _on_detect_psf(self):
        """Detect and extract beads in image depending on choosen parameters"""
        write_file_data("parameters_data.json", self.params) # Save parameters
        loaded_params = read_file_data("acquisition_data.json")
        physical_pixel = [1,1,1]
        if loaded_params:
            physical_pixel = [loaded_params["PhysicSizeZ"],loaded_params["PhysicSizeY"],loaded_params["PhysicSizeX"]]
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        image = current_layer.data
        threshold = self.params["Rel_threshold"]/100
        auto_threshold = self.params["auto_threshold"]
        threshold_choice = self.params["threshold_choice"]
        binary_image = None

        if self.params["selected_tool"] == 0 :
            show_info("Processing peak_local_max psf detection...")
            min_distance = self.params["Min_dist"]
            self.filtered_beads = detect_psf_peak_local_max(image, min_distance, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.params["selected_tool"] == 1:
            show_info("Processing blob_log psf detection...")
            sigma = self.params["Sigma"]
            self.filtered_beads = detect_psf_blob_log(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.params["selected_tool"] == 2 : 
            show_info("Processing blob_dog psf detection...")
            sigma = self.params["Sigma"]
            self.filtered_beads = detect_psf_blob_dog(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        else :
            show_info("Processing centroid psf detection...")
            self.filtered_beads,binary_image = detect_psf_centroid(image,threshold, auto_threshold,threshold_choice=threshold_choice)
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            self.rois,_ = extract_Region_Of_Interest(image,self.filtered_beads,bead_size=self.params["theorical_bead_size"],crop_factor=self.params["crop_factor"], rejection_zone=self.params["rejection_zone"],physical_pixel=physical_pixel)
            if self.filter_layer is None :
                self.filter_layer = self.viewer.add_shapes(self.rois,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
            else :
                self.viewer.layers.remove(self.filter_layer)
                self.filter_layer = self.viewer.add_shapes(self.rois,shape_type="rectangle",name="ROI",edge_color="blue",face_color="transparent")
            if self.filtered_layer is None :
                self.filtered_layer = self.viewer.add_points(self.filtered_beads,name="PSF detected", face_color='red', opacity=0.5, size=2)
            else : 
                self.filtered_layer.data = self.filtered_beads
        else :
            show_warning("No PSF found or incorrect format.")
        self.results_label.setText(f"Here are the results of the detection :\n- {len(self.filtered_beads)} bead(s) detected\n- {len(self.rois)} ROI(s) extracted")
    
    def _open_parameters_window(self):
        """Open the parameters window"""
        if self.count_windows == 0 :
            self.parameters_window = QDialog(self)
            self.parameters_window.setWindowTitle("Detection parameters")
            self.parameters_window.setModal(True)
            parameters_widget = Detection_Parameters_Widget(self.viewer, self.params)
            parameters_widget.signal.params_updated.connect(self.on_params_updated)
            self.parameters_window.finished.connect(self._on_parameters_window_closed)
            parameters_layout = QVBoxLayout()
            parameters_layout.addWidget(parameters_widget)
            self.parameters_window.setLayout(parameters_layout)
            self.parameters_window.show()
            self.count_windows += 1
    
    def _on_parameters_window_closed(self, result):
        """Catch the close event of the window and update the counter"""
        self.count_windows -= 1

    def on_params_updated(self, new_params):
        """Catch parameters modification and update params"""
        self.params = new_params
        print(f"Paramètres mis à jour : {self.params}")
        write_file_data("parameters_data.json", self.params)
        self.parameters_window.close()

    def erase_Layers(self):
        """Delete all layers made by this wiget"""
        if self.filter_layer : 
            self.viewer.layers.remove(self.filter_layer)
        if self.filtered_layer :
            self.viewer.layers.remove(self.filtered_layer)

    def get_logo_path(self,theme):
        logo_dir = Path(__file__).parent / "res" / "drawable"
        if theme =="dark" :
            return logo_dir / "logo_dark.png"
        else:
            return logo_dir / "logo_light.png"

    def on_theme_change(self):
        icon_path = self.get_logo_path(get_settings().appearance.theme)
        self.parameters_btn.setIcon(QIcon(str(icon_path)))
        self.parameters_btn.setIconSize(QSize(35,35))
        self.parameters_btn.setFixedSize(35, 35)