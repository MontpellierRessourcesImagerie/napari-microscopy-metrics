"""
This module contains a napari widgets form for microscope acquisition parameters
"""

import napari
import webbrowser

from qtpy.QtCore import Qt, Signal, QObject
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
)
from autooptions import Options
from autooptions import OptionsWidget

from microscopy_metrics.resolutionTools.theoretical_resolution import (
    TheoreticalResolution,
)
from questionary import form


class UpdateScaleSignal(QObject):
    """A class used to create a signal for updating scale informations in detection widget when changing layer or applying new scale."""

    scaleUpdate = Signal(list)


class ImageSizeWidget(QWidget):
    """A widget allowing user to setup scale informations for the view and save them for next session."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()
        self.signal = UpdateScaleSignal()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options)
        self.widget.addApplyButton(self.apply)
        self.widget.getApplyButton().setText("Apply and save scale")
        self.widget.getApplyButton().setToolTip(
            "Apply scale to actual view and save values for next session"
        )
        self.widget.setToolTip(
            "Enter for each axis the size represented by a single pixel (µm/px)"
        )
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setToolTip("Go to documentation")
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
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
        options = Options("Pixel size", "set image scale")
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
        self.signal.scaleUpdate.emit(
            [
                self.options.value("Pixel size Z"),
                self.options.value("Pixel size Y"),
                self.options.value("Pixel size X"),
            ]
        )


class MicroscopeParametersWidget(QWidget):
    """A widget allowing user to setup microscope parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options)
        self.widget.addApplyButton(lambda: None)
        self.widget.getApplyButton().setText("Save microscope parameters")
        self.widget.getApplyButton().setToolTip(
            "Apply parameters for analysis and save them for next session"
        )
        self.widget.setToolTip("Microscope's parameters used for acquisition")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc.setToolTip("Go to documentation")
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for microscope parameters and load previous analysis informations if exists.
        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options(
            "Microscope parameters", "register microscope parameters"
        )
        options.addChoice(
            name="Microscope type",
            choices=[
                x for x in TheoreticalResolution._microscopesClasses.keys()
            ],
            value="widefield",
        )
        options.addInt(name="Emission wavelength", value=450)
        options.addFloat(name="Refraction index", value=1.45)
        options.addFloat(name="Numerical aperture", value=1.0)
        options.load()
        return options

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/acquisition.html#microscope-acquisition-parameters"
        webbrowser.open(documentationPath)


class AcquisitionToolPage(QWidget):
    """A napari widget form for microscope acquisition parameters. It contains an ImageSizeWidget for setting scale informations and a MicroscopeParametersWidget for setting microscope informations.
    It also update scale informations in detection widget when changing layer or applying new scale.
    Args:
        viewer (napari.viewer.Viewer): The environment where the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.countWindows = 0
        self.labelShape = QLabel()
        self.initUi()
        self.viewer.layers.selection.events.active.connect(self.onLayerChanged)

    def initUi(self):
        """A method used to create the layout of the widget."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.acquisitionGroup = QGroupBox("Image parameters")
        self.groupLayout = QVBoxLayout()
        self.acquisitionGroup.setLayout(self.groupLayout)
        self.pixelSizeLayout = QVBoxLayout()
        self.lblPixelSize = QLabel("Enter pixel size (µm/px)")
        self.lblPixelSize.setStyleSheet("font-weight: bold")
        self.lblPixelSize.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )

        self.widgetPxS = ImageSizeWidget(self.viewer)
        self.onLayerChanged()
        self.pixelSizeLayout.addWidget(self.lblPixelSize)
        self.pixelSizeLayout.addWidget(self.widgetPxS)
        self.groupLayout.addLayout(self.pixelSizeLayout)

        self.groupLayout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.microscopeLayout = QVBoxLayout()
        self.titleOptionsMicroscope = QLabel("Microscope parameters:")
        self.titleOptionsMicroscope.setStyleSheet("font-weight: bold")
        self.titleOptionsMicroscope.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )

        self.widgetMicroChoice = MicroscopeParametersWidget(self.viewer)
        self.microscopeLayout.addWidget(self.titleOptionsMicroscope)
        self.microscopeLayout.addWidget(self.widgetMicroChoice)
        self.groupLayout.addLayout(self.microscopeLayout)

        self.groupLayout.addWidget(self.labelShape)

        layout.addWidget(self.acquisitionGroup)
        self.setLayout(layout)

    def onLayerChanged(self):
        """A method called when changing active layer. It update scale informations in detection widget if the new active layer is an image and update label with the shape of the new active image."""
        currentLayer = self.viewer.layers.selection.active
        if currentLayer is None or not isinstance(
            currentLayer, napari.layers.Image
        ):
            return
        image = currentLayer.data
        shape = image.shape
        self.labelShape.setText(
            f"Selected image shape : {shape[2]} x {shape[1]} x {shape[0]} px"
        )
