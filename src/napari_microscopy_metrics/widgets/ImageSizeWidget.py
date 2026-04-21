import napari
import webbrowser

from qtpy.QtCore import Qt, Signal, QObject
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QPushButton
from autooptions import Options, OptionsWidget

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.SizeDatas import SizeDatas


class UpdateScaleSignal(QObject):
    """A class used to create a signal for updating scale informations in detection widget when changing layer or applying new scale."""

    scaleUpdate = Signal(list)


class ImageSizeWidget(BaseWidget):
    """A widget allowing user to setup scale informations for the view and save them for next session."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)
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
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
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

    def createDatas(self):
        """A method to create a SizeDatas object with current scale values."""
        return SizeDatas(
            sizeX=self.options.value("Pixel size X"),
            sizeY=self.options.value("Pixel size Y"),
            sizeZ=self.options.value("Pixel size Z"),
        )
