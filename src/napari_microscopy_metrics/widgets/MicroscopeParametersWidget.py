import napari
import webbrowser
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QPushButton
from autooptions import Options, OptionsWidget

from microscopy_metrics.resolutionTools.theoretical_resolution import (
    TheoreticalResolution,
)

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.MicroscopeDatas import (
    MicroscopeDatas,
)


class MicroscopeParametersWidget(BaseWidget):
    """A widget allowing user to setup microscope parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

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
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
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

    def createDatas(self):
        """A method to create a MicroscopeDatas object with current microscope parameters values."""
        return MicroscopeDatas(
            microscopeType=self.options.value("Microscope type"),
            emissionWavelength=self.options.value("Emission wavelength"),
            refractiveIndex=self.options.value("Refraction index"),
            numericalAperture=self.options.value("Numerical aperture"),
        )
