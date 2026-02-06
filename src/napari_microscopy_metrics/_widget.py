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

class Microscopy_Metrics_QWidget(QWidget):
    """Main Widget of the Microscopy_Metrics module"""
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        #TabWidget for navigation between tools
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.detection_tool_page = Detection_Tool_Tab(self.viewer)
        self.tab.addTab(self.detection_tool_page,"Detection tool")

        #Creation of the layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.tab)