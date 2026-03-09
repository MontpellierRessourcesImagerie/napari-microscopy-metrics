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


class UpdateScaleSignal(QObject):
    scale_update = Signal(list)


class ImageSizeWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()
        self.signal = UpdateScaleSignal()
        self.signal.scale_update.emit([
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ])

    def createLayout(self):
        self.widget = OptionsWidget(self.viewer,self.options)
        self.widget.addApplyButton(self.apply)
        self.widget.mainLayout.itemAt(3).widget().setText("Appy and save scale")
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        options = Options("Pixel size","set image scale")
        options.addFloat(name="Pixel size X", value=0.069)
        options.addFloat(name="Pixel size Y", value=0.069)
        options.addFloat(name="Pixel size Z", value=0.1)
        options.load()
        return options

    def apply(self):
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = [
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ]
        self.signal.scale_update.emit([
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ])


class MicroscopeParametersWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        self.widget = OptionsWidget(self.viewer,self.options)
        self.widget.addApplyButton(lambda : None)
        self.widget.mainLayout.itemAt(4).widget().setText("Save microscope parameters")
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        options = Options("Microscope parameters","register microscope parameters")
        options.addChoice(name="Microscope type",choices=[x for x in Theoretical_Resolution._microscopes_classes.keys()],value="widefield")
        options.addInt(name="Emission wavelength",value=450)
        options.addFloat(name="Refraction index", value=1.45)
        options.addFloat(name="Numerical aperture", value=1.0)
        options.load()
        return options


class Acquisition_tool_page(QWidget):
    """The main widget for microscope acquisition parameters

    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.count_windows = 0
        self.label_shape = QLabel()
        self.init_ui()
        self.viewer.layers.selection.events.active.connect(self._on_layer_changed)

    def init_ui(self):
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

        self.widget_PxS = ImageSizeWidget(self.viewer)
        self._on_layer_changed()
        self.pixel_size_layout.addWidget(self.lbl_pixel_size)
        self.pixel_size_layout.addWidget(self.widget_PxS)
        self.group_layout.addLayout(self.pixel_size_layout)

        self.group_layout.addSpacerItem(QSpacerItem(20,40,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.microscope_layout = QVBoxLayout()
        self.title_options_microscope = QLabel("Microscope parameters:")
        self.title_options_microscope.setStyleSheet("font-weight: bold")
        self.title_options_microscope.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.widget_micro_choice = MicroscopeParametersWidget(self.viewer)
        self.microscope_layout.addWidget(self.title_options_microscope)
        self.microscope_layout.addWidget(self.widget_micro_choice)
        self.group_layout.addLayout(self.microscope_layout)
        
        self.group_layout.addWidget(self.label_shape)

        layout.addWidget(self.acquisition_group)
        self.setLayout(layout)

    def _on_layer_changed(self):
        """updating image shape values when changing layer"""
        current_layer = self.viewer.layers.selection.active
        if current_layer is None or not isinstance(current_layer, napari.layers.Image):
            return
        image = current_layer.data
        shape = image.shape
        self.label_shape.setText(f"Selected image shape : {shape[2]} x {shape[1]} x {shape[0]} px")
