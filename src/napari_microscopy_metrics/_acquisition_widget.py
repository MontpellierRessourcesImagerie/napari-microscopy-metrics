"""
This module contains a napari widgets form for microscope acquisition parameters 
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
from microscopy_metrics.utils import *
import napari
from napari.utils.notifications import *
from .json_utils import *
from autooptions import *

class Acquisition_tool_page(QWidget):
    """ The main widget for microscope acquisition parameters
    
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
            "PhysicSizeX":10,
            "PhysicSizeY":6,
            "PhysicSizeZ":3,
            "ShapeX":10,
            "ShapeY":5,
            "ShapeZ":0,
            "Microscope_type":"widefield",
            "Emission_Wavelength":450,
            "Refractive_index":1.45,
            "Numerical_aperture":1
        }

        #Read and restore datas if exist
        loaded_params = read_file_data("acquisition_data.json")
        if loaded_params:
            self.params.update(loaded_params)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.acquisition_group = QGroupBox("Image parameters")
        self.group_layout = QVBoxLayout()
        self.acquisition_group.setLayout(self.group_layout)

        self.pixel_size_layout = QVBoxLayout()
        self.lbl_pixel_size = QLabel("Enter pixel size (µm/px)")
        self.lbl_pixel_size.setStyleSheet("font-weight: bold")
        self.lbl_pixel_size.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.options_PxS = Options("Pixel size", "Median Filter")
        self.options_PxS.addFloat(name="Pixel size X",value=self.params["PhysicSizeX"])
        self.options_PxS.addFloat(name="Pixel size Y",value=self.params["PhysicSizeY"])
        self.options_PxS.addFloat(name="Pixel size Z",value=self.params["PhysicSizeZ"])
        self.widget_PxS = OptionsWidget(self.viewer,self.options_PxS)
        self.label_shape = QLabel()
        self._on_layer_changed()
        self.pixel_size_layout.addWidget(self.lbl_pixel_size)
        self.pixel_size_layout.addWidget(self.widget_PxS)
        self.pixel_size_layout.addWidget(self.label_shape)
        self.group_layout.addLayout(self.pixel_size_layout)

        self.microscope_layout = QVBoxLayout()
        self.title_options_microscope = QLabel("Microscope parameters:")
        self.title_options_microscope.setStyleSheet("font-weight: bold")
        self.title_options_microscope.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.options_microscope = Options("Micoscope choice", "Median Filter")
        self.options_microscope.addChoice(name="Microscope type",choices=["widefield","confocal"],value=self.params["Microscope_type"])
        self.options_microscope.addInt(name="Emission wavelength", value=self.params["Emission_Wavelength"])
        self.options_microscope.addFloat(name="Refraction index", value=self.params["Refractive_index"])
        self.options_microscope.addFloat(name="Numerical aperture", value = self.params["Numerical_aperture"])
        self.widget_micro_choice = OptionsWidget(self.viewer,self.options_microscope)
        self.widget_micro_choice.addApplyButton(self._on_apply)
        self.microscope_layout.addWidget(self.title_options_microscope)
        self.microscope_layout.addWidget(self.widget_micro_choice)
        self.group_layout.addLayout(self.microscope_layout)
        
        layout.addWidget(self.acquisition_group)
        self.setLayout(layout)

        self.viewer.layers.selection.events.active.connect(self._on_layer_changed)

    def _on_apply(self):
        """Save acquisition datas to json file"""
        self.update_params()
        write_file_data("acquisition_data.json", self.params) # Save parameters
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = [self.params["PhysicSizeZ"],self.params["PhysicSizeY"],self.params["PhysicSizeX"]]

    def _on_layer_changed(self):
        """updating image shape values when changing layer"""
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image) : # Catch if Image layer not selected
            return 
        image = current_layer.data
        shape = image.shape
        self.label_shape.setText(f"{shape[2]} x {shape[1]} x {shape[0]} px")
        self.params["ShapeZ"] = shape[0]
        self.params["ShapeY"] = shape[1]
        self.params["ShapeX"] = shape[2]

    def update_params(self):
        """Function to update acquisition parameters"""
        self.widget_PxS.transferValues()
        self.widget_micro_choice.transferValues()
        self.params["PhysicSizeX"] = self.options_PxS.value("Pixel size X")
        self.params["PhysicSizeY"] = self.options_PxS.value("Pixel size Y")
        self.params["PhysicSizeZ"] = self.options_PxS.value("Pixel size Z")
        self.params["Emission_Wavelength"] = self.options_microscope.value("Emission wavelength")
        self.params["Microscope_type"] = self.options_microscope.value("Microscope type")
        self.params["Numerical_aperture"] = self.options_microscope.value("Numerical aperture")
        self.params["Refractive_index"] = self.options_microscope.value("Refraction index")

