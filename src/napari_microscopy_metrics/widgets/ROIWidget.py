import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSizePolicy, QVBoxLayout, QPushButton, QSlider, QLabel

from autooptions import Options, OptionsWidget

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.ROIDatas import ROIDatas


class RoiWidget(BaseWidget):
    """A widget allowing user to setup region of interest parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.cropFactor = QSlider(Qt.Horizontal)
        self.cropFactor.setRange(1, 10)
        self.cropFactor.setValue(self.optionsSliders.value("crop factor"))
        self.cropFactorLabel = QLabel(
            "Crop factor: " + str(self.cropFactor.value())
        )
        self.thresholdIntensity = QSlider(Qt.Horizontal)
        self.thresholdIntensity.setRange(0, 100)
        self.thresholdIntensity.setValue(
            self.optionsSliders.value("threshold intensity")
        )
        self.thresholdIntensityLabel = QLabel(
            "Threshold mean intensity: " + str(self.thresholdIntensity.value())
        )
        self.widget.mainLayout.addWidget(self.cropFactorLabel)
        self.widget.mainLayout.addWidget(self.cropFactor)
        self.widget.mainLayout.addWidget(self.thresholdIntensityLabel)
        self.widget.mainLayout.addWidget(self.thresholdIntensity)
        self.widget.addApplyButton(self.apply)
        self.widget.setToolTip(
            "Parameters for ROI extraction and bead's rejecting criterions"
        )
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.cropFactor.valueChanged.connect(self.updateCropFactor)
        self.thresholdIntensity.valueChanged.connect(
            self.updateThresholdIntensity
        )

    @classmethod
    def getOptions(cls):
        """A class method which create entries for region of interest informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options(
            "Extraction parameters", "Set parameters for extraction"
        )
        options.addFloat(name="Theoretical bead size (µm)", value=0.6)
        options.addFloat(name="Z axis rejection margin (µm)", value=0.5)
        options.addFloat(name="Inner annulus distance to bead (µm)", value=1.0)
        options.addFloat(name="Annulus thickness (µm)", value=2.0)
        options.load()
        return options

    def getSliders(self):
        """A method which create entries for region of interest sliders informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        optionsSliders = Options(
            "Crop factor value", "Store value of crop factor"
        )
        optionsSliders.addInt(name="crop factor", value=5)
        optionsSliders.addInt(name="threshold intensity", value=95)
        optionsSliders.load()
        return optionsSliders

    def apply(self):
        """Called on validation to save optionSliders with current sliders value."""
        self.optionsSliders.save()

    def updateCropFactor(self, value):
        """Updates the label for crop factor and assign the value to optionSliders

        Args:
            value (int): Value of the crop factor.
        """
        self.cropFactorLabel.setText("Crop factor: " + str(value))
        self.optionsSliders.items["crop factor"]["value"] = value

    def updateThresholdIntensity(self, value):
        """Updates the label for threshold mean intensity and assign the value to optionSliders

        Args:
            value (int): Value of the mean intensity threshold.
        """
        self.thresholdIntensityLabel.setText(
            "Threshold mean intensity: " + str(value)
        )
        self.optionsSliders.items["threshold intensity"]["value"] = value

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/detection.html#region-of-interest-parameters"
        webbrowser.open(documentationPath)

    def createDatas(self):
        """A method to create a ROIDatas object with current region of interest parameters values."""
        return ROIDatas(
            beadSize=self.options.value("Theoretical bead size (µm)"),
            rejectionDistance=self.options.value(
                "Z axis rejection margin (µm)"
            ),
            ringInnerDistance=self.options.value(
                "Inner annulus distance to bead (µm)"
            ),
            ringThickness=self.options.value("Annulus thickness (µm)"),
            cropFactor=self.optionsSliders.value("crop factor"),
            thresholdIntensity=self.optionsSliders.value("threshold intensity")
            / 100,
        )
