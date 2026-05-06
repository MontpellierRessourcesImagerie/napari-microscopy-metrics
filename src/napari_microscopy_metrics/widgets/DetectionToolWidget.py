import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QStackedWidget,
    QWidget,
    QLabel,
    QSlider,
    QSizePolicy,
)
from autooptions import Options, OptionsWidget
from microscopy_metrics.detectionTools.detection_tool import DetectionTool

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.DetectionDatas import DetectionDatas


class DetectionToolWidget(BaseWidget):
    """A widget allowing user to choose the detection tool he wants to use with related parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        self.paramsStack = None
        super().__init__(viewer)

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options, client=self)
        self.toolChoiceWidget = self.widget.widgets["Detection tool"][1]
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.paramsStack = QStackedWidget()
        self.peakMethodWidget = QWidget()
        self.peakMethodLayout = QVBoxLayout()
        self.peakMethodLayout.setContentsMargins(0, 0, 0, 0)
        self.peakMethodLayout.setSpacing(2)
        self.minDistanceDetection = QSlider(Qt.Horizontal)
        self.minDistanceDetection.setRange(0, 20)
        self.minDistanceDetection.setValue(
            self.optionsSliders.value("Min dist")
        )
        self.minDistanceDetection.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )
        self.minDistanceLabel = QLabel(
            "Minimal distance: " + str(self.minDistanceDetection.value())
        )
        self.minDistanceLabel.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )
        self.peakMethodLayout.addWidget(self.minDistanceLabel)
        self.peakMethodLayout.addWidget(self.minDistanceDetection)
        self.peakMethodWidget.setLayout(self.peakMethodLayout)
        self.blobMethodWidget = QWidget()
        self.blobMethodLayout = QVBoxLayout()
        self.blobSigmaSlider = QSlider(Qt.Horizontal)
        self.blobSigmaSlider.setRange(1, 10)
        self.blobSigmaSlider.setValue(self.optionsSliders.value("Sigma"))
        self.blobSigmaLabel = QLabel(
            "Sigma: " + str(self.blobSigmaSlider.value())
        )
        self.blobMethodLayout.addWidget(self.blobSigmaLabel)
        self.blobMethodLayout.addWidget(self.blobSigmaSlider)
        self.blobMethodWidget.setLayout(self.blobMethodLayout)
        self.centroidMethodWidget = QWidget()
        self.centroidMethodLayout = QVBoxLayout()
        self.centroidMethodWidget.setLayout(self.centroidMethodLayout)
        self.paramsStack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.paramsStack.addWidget(self.peakMethodWidget)
        self.paramsStack.addWidget(self.blobMethodWidget)
        self.paramsStack.addWidget(self.centroidMethodWidget)
        self.widget.mainLayout.addWidget(self.paramsStack)
        self.widget.addApplyButton(self.apply)
        self.widget.setToolTip("Select a detection tool")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.minDistanceDetection.valueChanged.connect(self.updateMinDistance)
        self.blobSigmaSlider.valueChanged.connect(self.updateSigma)

    def getOptions(self):
        """A class method which create entries for detection tool informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options(
            "Detection Parameters", "Set parameters for detection tool"
        )
        options.addChoice(
            name="Detection tool",
            value="Centroids",
            choices=[x for x in DetectionTool._detectionClasses],
            callback=self.selectedAction,
        )
        options.load()
        return options

    def getSliders(self):
        """A method which create entries for detection tool sliders informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        optionsSliders = Options("Sliders value", "Store value of sliders")
        optionsSliders.addInt(name="Min dist", value=1)
        optionsSliders.addInt(name="Sigma", value=3)
        optionsSliders.load()
        return optionsSliders

    def selectedAction(self, value):
        """Update the display for selected tool.

        Args:
            value (int): Index of the selection.
        """
        if value == "peak local maxima":
            index = 0
        elif value == "Laplacian of Gaussian" or value == "Difference of Gaussian":
            index = 1
        elif value == "Centroids":
            index = 2
        if self.paramsStack is not None:
            self.paramsStack.setCurrentIndex(index)

    def apply(self):
        """Called on click button to save option sliders with actual sliders values."""
        self.optionsSliders.save()

    def updateMinDistance(self, value):
        """Update the label for minimal distance and assign the value in optionSliders

        Args:
            value (int): Minimal distance value
        """
        self.minDistanceLabel.setText("Minimal distance: " + str(value))
        self.optionsSliders.items["Min dist"]["value"] = value

    def updateSigma(self, value):
        """Update the label for sigma and assign the value in optionSliders

        Args:
            value (int): Sigma value
        """
        self.blobSigmaLabel.setText("Sigma: " + str(value))
        self.optionsSliders.items["Sigma"]["value"] = value

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/detection.html#detection-parameters"
        webbrowser.open(documentationPath)

    def createDatas(self):
        """A method to create a DetectionToolDatas object with current detection tool and parameters values."""
        return DetectionDatas(
            detectionTool=self.options.value("Detection tool"),
            minDist=self.optionsSliders.value("Min dist"),
            sigma=self.optionsSliders.value("Sigma"),
        )
