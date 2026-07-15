import napari
import webbrowser
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QPushButton
from autooptions import Options, OptionsWidget
from napari.utils.notifications import show_warning
from microscopy_metrics.resolutionTools.theoretical_resolution import (
    TheoreticalResolution,
)
from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget


class MicroscopeParametersWidget(BaseWidget):
    """A widget allowing user to setup microscope parameters.
    
    Attributes:
        backupNumericalAperture (float): A backup value for the numerical aperture to restore in case of invalid input.
        backupRefractionIndex (float): A backup value for the refraction index to restore in case of invalid input.
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)
        self.backupNumericalAperture = self.options.value("Numerical aperture")
        self.backupRefractionIndex = self.options.value("Refraction index")

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options, client=self)
        self.widget.addApplyButton(self.apply)
        self.widget.getApplyButton().setText("Save microscope parameters")
        self.widget.getApplyButton().setToolTip(
            "Apply parameters for analysis and save them for next session"
        )
        self.widget.setToolTip("Microscope's parameters used for acquisition")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        """A class method which creates entries for microscope parameters and load previous analysis informations if exists.
        
        Returns:
            options (Options): The object that contains every widget informations.
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
        options.addInt(name="Excitation wavelength", value=225)
        options.addFloat(name="Refraction index", value=1.45)
        options.addFloat(name="Numerical aperture", value=1.0)
        options.load()
        return options
    
    def apply(self):
        """A method to apply microscope parameters and save them for next session. Also checks if the numerical aperture is lower than the refraction index and restore previous values if not."""
        if self.options.value("Numerical aperture") >= self.options.value("Refraction index"):
            show_warning("Numerical aperture should be lower than refraction index.")
            self.options.setValue("Numerical aperture", self.backupNumericalAperture)
            self.options.setValue("Refraction index", self.backupRefractionIndex)
            print(self.options.value("Numerical aperture"), self.options.value("Refraction index"))
            self.options.save()
            self.options.load()
            self.widget.widgets["Numerical aperture"][1].setText(str(self.options.value("Numerical aperture")))
            self.widget.widgets["Refraction index"][1].setText(str(self.options.value("Refraction index")))
        else:
            self.backupNumericalAperture = self.options.value("Numerical aperture")
            self.backupRefractionIndex = self.options.value("Refraction index")


    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/acquisition.html#microscope-acquisition-parameters"
        webbrowser.open(documentationPath)
    
    def toDict(self):
        """A method to create a dict with current microscope parameters values."""
        return {
            "microscopeType": self.options.value("Microscope type"),
            "emissionWavelength": self.options.value("Emission wavelength"),
            "refractiveIndex": self.options.value("Refraction index"),
            "numericalAperture": self.options.value("Numerical aperture"),
            "excitationWavelength": self.options.value("Excitation wavelength"),
        }
