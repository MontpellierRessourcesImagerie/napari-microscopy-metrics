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
import napari
from napari.utils.notifications import *
from .json_utils import *
from autooptions import *

class Metrics_tool_page(QWidget):
    """ The main widget for microscope metrics parameters
    
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
            "Gaussian_type":"1D",
        }

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.group_metrics = QGroupBox("Metrics parameters")
        self.group_layout = QVBoxLayout()
        self.group_metrics.setLayout(self.group_layout)
        self.layout_parameters = QVBoxLayout()
        self.options_fitting = Options("Fitting options", "Median Filter")
        self.options_fitting.addChoice(name="fitting_type",choices=["1D","2D","3D"],value=self.params["Gaussian_type"])
        self.widget_fitting_choice = OptionsWidget(self.viewer,self.options_fitting)
        self.layout_parameters.addWidget(self.widget_fitting_choice)
        self.group_layout.addLayout(self.layout_parameters)
        
        self.group_results = QGroupBox("Mean metrics measured")
        self.layout_results = QVBoxLayout()
        self.results_label = QLabel("No metric mesured yet.")
        self.layout_results.addWidget(self.results_label)
        self.group_results.setLayout(self.layout_results)

        layout.addWidget(self.group_metrics)
        layout.addWidget(self.group_results)
        layout.addStretch()
        self.setLayout(layout)

    def print_results(self,SBR):
        """Display metrics measures to widget"""
        text = f"- Signal to background ratio: {SBR:.2f}"
        self.results_label.setText(text)
