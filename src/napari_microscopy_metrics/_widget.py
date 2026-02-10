"""
This module contains a napari widgets for PSF analysis:
- A QWidget class for performing PSF detection using two methods (centroids and peak_local_max)

"""
from typing import TYPE_CHECKING, Optional
import types
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject
from qtpy.QtWidgets import *
import napari
from ._detection_tool_widget import *
from._acquisition_widget import *
from ._metrics_widget import *

class Microscopy_Metrics_QWidget(QWidget):
    """Main Widget of the Microscopy_Metrics module"""
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.parameters_detection = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
            "theorical_bead_size":10,
            "crop_factor":5,
            "selected_tool":0,
            "auto_threshold":False,
            "rejection_zone":10,
            "distance_annulus" : 10,
            "thickness_annulus": 10
        }
        #Read and restore datas if exist
        loaded_params = read_file_data("parameters_data.json")
        if loaded_params:
            self.parameters_detection.update(loaded_params)

        self.parameters_acquisition = {
            "PhysicSizeX":10,
            "PhysicSizeY":6,
            "PhysicSizeZ":3,
            "ShapeX":10,
            "ShapeY":5,
            "ShapeZ":0,
            "Microscope_type":"widefield",
            "Emission_Wavelength":450,
            "Refractive_index":10,
            "Numerical_aperture":1
        }
        #Read and restore datas if exist
        loaded_params = read_file_data("acquisition_data.json")
        if loaded_params:
            self.parameters_acquisition.update(loaded_params)
        
        self.filtered_layer = None
        self.filter_layer = None
        self.filtered_beads = None
        self.rois = None
        self.cropped_layers = []
        self.working_layer = None
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #TabWidget for navigation between tools
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.setDocumentMode(True)

        self.acquisition_tool_page = Acquisition_tool_page(self.viewer)
        self.acquisition_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.acquisition_tool_page,"Acquisition parameters")
        self.detection_tool_page = Detection_Tool_Tab(self.viewer)
        self.detection_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.detection_tool_page,"Detection parameters")
        self.metrics_tool_page = Metrics_tool_page(self.viewer)
        self.metrics_tool_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.addTab(self.metrics_tool_page,"Metrics parameters")

        #Button to run global analyze
        self.run_btn = QPushButton("Run")
        self.run_btn.setStyleSheet("background-color : green")
        self.run_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        #Creation of the layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)

        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.run_btn)

        self.run_btn.pressed.connect(self._on_run)

    def _on_run(self):
        print("Analysing...")
        self._on_detect_psf()
        self._on_crop_psf()
        self._on_SBR()


    def _on_detect_psf(self):
        """Detect and extract beads in image depending on choosen parameters"""
        self.parameters_detection = self.detection_tool_page.params
        self.parameters_acquisition = self.acquisition_tool_page.params
        
        self.working_layer = self.viewer.layers.selection.active
        if self.working_layer is None or not isinstance(self.working_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        
        image = self.working_layer.data
        threshold = self.parameters_detection["Rel_threshold"]/100
        auto_threshold = self.parameters_detection["auto_threshold"]
        binary_image = None
        physical_pixel = [self.parameters_acquisition["PhysicSizeZ"],self.parameters_acquisition["PhysicSizeY"],self.parameters_acquisition["PhysicSizeX"]]
        threshold_choice = self.parameters_detection["threshold_choice"]
        self.detection_tool_page.erase_Layers()

        if self.parameters_detection["selected_tool"] == 0 :
            show_info("Processing peak_local_max psf detection...")
            min_distance = self.parameters_detection["Min_dist"]
            self.filtered_beads = detect_psf_peak_local_max(image, min_distance, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.parameters_detection["selected_tool"] == 1:
            show_info("Processing blob_log psf detection...")
            sigma = self.parameters_detection["Sigma"]
            self.filtered_beads = detect_psf_blob_log(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        elif self.parameters_detection["selected_tool"] == 2 : 
            show_info("Processing blob_dog psf detection...")
            sigma = self.parameters_detection["Sigma"]
            self.filtered_beads = detect_psf_blob_dog(image, sigma, threshold,auto_threshold,threshold_choice=threshold_choice)
        else :
            show_info("Processing centroid psf detection...")
            self.filtered_beads,binary_image = detect_psf_centroid(image,threshold, auto_threshold,threshold_choice=threshold_choice)
        
        if isinstance(self.filtered_beads, np.ndarray) and self.filtered_beads.size > 0 :
            self.rois = extract_Region_Of_Interest(image,self.filtered_beads,bead_size=self.parameters_detection["theorical_bead_size"],crop_factor=self.parameters_detection["crop_factor"], rejection_zone=self.parameters_detection["rejection_zone"], physical_pixel=physical_pixel)
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
        
    def _on_crop_psf(self):
        """Crop the image along ROIs and generate a new layer for each"""
        if self.working_layer is None or not isinstance(self.working_layer, napari.layers.Image) : # Catch if Image layer not selected
            show_error("Please, select a valid layer of type Image")
            return 
        self.cropped_layers = []
        for i,roi in enumerate(self.rois):
            data = self.working_layer.data[...,roi[0][1]:roi[2][1],roi[0][2]:roi[1][2]]
            self.cropped_layers.append(data)

    def _on_SBR(self):
        """Measure de mean signal to background ratio of ROIs in the image"""
        mean_SBR,SBR = signal_to_background_ratio(self.cropped_layers,0,0)
        print(mean_SBR,SBR)
