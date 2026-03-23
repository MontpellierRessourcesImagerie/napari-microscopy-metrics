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
import napari
from napari.utils.notifications import *
from .json_utils import *
from autooptions import *
from microscopy_metrics.theoretical_resolution import TheoreticalResolution
import webbrowser



class UpdateScaleSignal(QObject):
    """Signal sent to main widget when pixel scale is updated"""
    scaleUpdate = Signal(list)


class ImageSizeWidget(QWidget):
    """A widget allowing user to setup the scaling of the image. Send a signal to automatically resize the actual view.
    """
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()
        self.signal = UpdateScaleSignal()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis.
        """
        self.widget = OptionsWidget(self.viewer,self.options)
        self.widget.addApplyButton(self.apply)
        self.widget.mainLayout.itemAt(3).widget().setText("Apply and save scale")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24,24)
        self.btnDoc
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.btnDoc,alignment=Qt.AlignRight)
        self.setLayout(layout)
        
    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/acquisition.html#image-scaling-parameters"
        webbrowser.open(documentationPath)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for scale informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options("Pixel size","set image scale")
        options.addFloat(name="Pixel size X", value=0.069)
        options.addFloat(name="Pixel size Y", value=0.069)
        options.addFloat(name="Pixel size Z", value=0.1)
        options.load()
        return options

    def apply(self):
        """Called on validation, resize layers of the view and emit signal to application for updating detection widget."""
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = [
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ]
        self.viewer.reset_view()
        self.signal.scaleUpdate.emit([
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ])


class MicroscopeParametersWidget(QWidget):
    """A widget allowing user to setup microscope parameters."""
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis.
        """
        self.widget = OptionsWidget(self.viewer,self.options)
        self.widget.addApplyButton(lambda : None)
        self.widget.mainLayout.itemAt(4).widget().setText("Save microscope parameters")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24,24)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.btnDoc,alignment=Qt.AlignRight)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for microscope informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options("Microscope parameters","register microscope parameters")
        options.addChoice(name="Microscope type", choices=[x for x in TheoreticalResolution._microscopesClasses.keys()], value="widefield")
        options.addInt(name="Emission wavelength",value=450)
        options.addFloat(name="Refraction index", value=1.45)
        options.addFloat(name="Numerical aperture", value=1.0)
        options.load()
        return options

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/acquisition.html#microscope-acquisition-parameters"
        webbrowser.open(documentationPath)


class AcquisitionToolPage(QWidget):
    """The main widget for microscope acquisition parameters

    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.countWindows = 0
        self.labelShape = QLabel()
        self.initUi()
        self.viewer.layers.selection.events.active.connect(self.onLayerChanged)

    def initUi(self):
        """Initialize user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.acquisitionGroup = QGroupBox("Image parameters")
        self.groupLayout = QVBoxLayout()
        self.acquisitionGroup.setLayout(self.groupLayout)
        self.pixelSizeLayout = QVBoxLayout()
        self.lblPixelSize = QLabel("Enter pixel size (µm/px)")
        self.lblPixelSize.setStyleSheet("font-weight: bold")
        self.lblPixelSize.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.widgetPxS = ImageSizeWidget(self.viewer)
        self.onLayerChanged()
        self.pixelSizeLayout.addWidget(self.lblPixelSize)
        self.pixelSizeLayout.addWidget(self.widgetPxS)
        self.groupLayout.addLayout(self.pixelSizeLayout)

        self.groupLayout.addSpacerItem(QSpacerItem(20,40,QSizePolicy.Expanding,QSizePolicy.Minimum))

        self.microscopeLayout = QVBoxLayout()
        self.titleOptionsMicroscope = QLabel("Microscope parameters:")
        self.titleOptionsMicroscope.setStyleSheet("font-weight: bold")
        self.titleOptionsMicroscope.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.widgetMicroChoice = MicroscopeParametersWidget(self.viewer)
        self.microscopeLayout.addWidget(self.titleOptionsMicroscope)
        self.microscopeLayout.addWidget(self.widgetMicroChoice)
        self.groupLayout.addLayout(self.microscopeLayout)
        
        self.groupLayout.addWidget(self.labelShape)

        layout.addWidget(self.acquisitionGroup)
        self.setLayout(layout)

    def onLayerChanged(self):
        """updating image shape values when changing layer"""
        currentLayer = self.viewer.layers.selection.active
        if currentLayer is None or not isinstance(currentLayer, napari.layers.Image):
            return
        image = currentLayer.data
        shape = image.shape
        self.labelShape.setText(f"Selected image shape : {shape[2]} x {shape[1]} x {shape[0]} px")
