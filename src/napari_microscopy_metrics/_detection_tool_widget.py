"""
This module contains a napari widgets for PSF detection
"""

import napari
import webbrowser
import numpy as np
from pathlib import Path

from qtpy.QtGui import QIcon
from autooptions import Options
from autooptions import OptionsWidget
from napari.settings import get_settings
from napari.qt.threading import create_worker
from qtpy.QtCore import Qt, QSize, Signal, QObject
from napari.utils.notifications import show_warning
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QSizePolicy,
    QStackedWidget,
    QGroupBox,
    QSlider,
)

from microscopy_metrics.detection import Detection
from microscopy_metrics.thresholdTools.threshold_tool import Threshold
from microscopy_metrics.detectionTools.detection_tool import DetectionTool
from microscopy_metrics.detectionTools.peakLocalMax import PeakLocalMaxDetector


class ParamsSignal(QObject):
    """Class for the declaration of update parameters signal"""

    params_updated = Signal(dict)


class DetectionToolWidget(QWidget):
    """A widget allowing user to choose the detection tool he wants to use with related parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.optionsSliders = self.getSliders()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options)
        self.toolChoiceWidget = self.widget.widgets["Detection tool"]
        self.toolChoiceWidget.currentTextChanged.connect(self.selectedAction)
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
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc.setToolTip("Go to documentation")
        layout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.minDistanceDetection.valueChanged.connect(self.updateMinDistance)
        self.blobSigmaSlider.valueChanged.connect(self.updateSigma)

    @classmethod
    def getOptions(cls):
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
        index = self.toolChoiceWidget.currentIndex()
        if index >= 2:
            index = index - 1
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


class ThresholdWidget(QWidget):
    """A widget allowing user to choose the Threshold he wants to apply to the image for analysis."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.optionsSliders = self.getSliders()
        self.widget = None
        self.createLayout()
        self.layer = None
        self.oldContrastLimits = []

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options)
        self.toolChoiceWidget = self.widget.widgets["Threshold"]
        self.toolChoiceWidget.currentTextChanged.connect(self.selectedAction)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.paramsStack = QStackedWidget()
        self.thresholdRelWidget = QWidget()
        self.thresholdRelLayout = QVBoxLayout()
        self.thresholdRelLayout.setContentsMargins(0, 0, 0, 0)
        self.thresholdRelLayout.setSpacing(2)
        self.thresholdRel = QSlider(Qt.Horizontal)
        self.thresholdRel.setRange(0, 100)
        self.thresholdRel.setValue(self.optionsSliders.value("threshold"))
        self.thresholdRelLabel = QLabel(
            "Relative threshold: " + str(self.thresholdRel.value() / 100)
        )
        self.thresholdRelLayout.addWidget(self.thresholdRelLabel)
        self.thresholdRelLayout.addWidget(self.thresholdRel)
        self.thresholdRelWidget.setLayout(self.thresholdRelLayout)
        self.emptyWidget = QWidget()
        self.emptyLayout = QVBoxLayout()
        self.emptyWidget.setLayout(self.emptyLayout)
        self.paramsStack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.paramsStack.addWidget(self.thresholdRelWidget)
        self.paramsStack.addWidget(self.emptyWidget)
        self.widget.mainLayout.addWidget(self.paramsStack)
        self.widget.addApplyButton(self.apply)
        self.widget.setToolTip("Choose a threshold for the detection")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc.setToolTip("Go to documentation")
        layout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.thresholdRel.valueChanged.connect(self.updateThreshold)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for threshold informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options(
            "Threshold parameters", "Set parameters for threshold"
        )
        options.addChoice(
            name="Threshold",
            value="otsu",
            choices=[x for x in Threshold._thresholdClasses],
        )
        options.load()
        return options

    def getSliders(self):
        """A method which create entries for threshold sliders informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        optionsSliders = Options("Sliders value", "Store value of sliders")
        optionsSliders.addInt(name="threshold", value=50)
        optionsSliders.load()
        return optionsSliders

    def selectedAction(self, value):
        """Update the display for selected threshold.

        Args:
            value (string): label of the selection.
        """
        if value == "manual":
            self.paramsStack.setCurrentIndex(0)
        else:
            self.paramsStack.setCurrentIndex(1)

    def apply(self):
        """Called on validation to save optionSliders with current sliders value and update the view with thresholded image."""
        self.optionsSliders.save()
        if self.toolChoiceWidget.currentText() != "manual":
            self.displayThreshold(self.toolChoiceWidget.currentText())

    def updateThreshold(self, value):
        """Update the label for relative threshold, assign the value in optionSliders and update the view with new thresholded image.

        Args:
            value (int): The actual value of the slider.
        """
        self.thresholdRelLabel.setText(
            "Relative threshold: " + str(value / 100)
        )
        self.optionsSliders.items["threshold"]["value"] = value
        self.displayThreshold("manual", value=value / 100)

    def displayThreshold(self, thresholdStr, value=0.5):
        """A method to change layer properties to display (or not) a render view of the thresholded image with actual properties.

        Args:
            thresholdStr (Str): The label of the selected threshold.
            value (float, optional): Relative value of the threshold. Defaults to 0.5.
        """
        if isinstance(
            self.viewer.layers.selection.active, napari.layers.Image
        ):
            if (
                self.layer != self.viewer.layers.selection.active
                and self.layer is not None
            ):
                self.layer.contrast_limits = self.oldContrastLimits
                self.layer.colormap = "gray"
                self.layer.blending = "additive"
                self.layer = None
            if self.layer is None or self.oldContrastLimits is None:
                self.layer = self.viewer.layers.selection.active
                self.oldContrastLimits = self.layer.contrast_limits
            threshold = Threshold.getInstance(thresholdStr)
            if thresholdStr == "manual":
                threshold._relThreshold = value
            valueThreshold = threshold.getThreshold(self.layer.data)
            self.layer.contrast_limits = [
                max(
                    min(
                        valueThreshold + np.min(self.layer.data),
                        self.oldContrastLimits[1] - 1,
                    ),
                    self.oldContrastLimits[0],
                ),
                self.oldContrastLimits[1],
            ]
            self.layer.colormap = "HiLo"
            self.layer.blending = "additive"

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/detection.html#threshold-parameters"
        webbrowser.open(documentationPath)


class RoiWidget(QWidget):
    """A widget allowing user to setup region of interest parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.optionsSliders = self.getSliders()
        self.widget = None
        self.createLayout()

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
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc.setToolTip("Go to documentation")
        layout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
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


class DetectionParametersWidget(QWidget):
    """A widget for processing PSF detection and extraction

    Parameters
    ----------
    viewer : napari.viewer.Viewer
        The napari viewer were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.signal = ParamsSignal()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.detectionGroup = QGroupBox("Detection parameters")
        self.groupLayout = QVBoxLayout()
        self.detectionGroup.setLayout(self.groupLayout)

        self.detectionToolLayout = QVBoxLayout()
        self.detectionToolWidget = DetectionToolWidget(self.viewer)
        self.detectionToolLayout.addWidget(self.detectionToolWidget)
        self.groupLayout.addLayout(self.detectionToolLayout)

        self.layer = None
        self.oldContrastLimits = None

        self.thresholdGroup = QGroupBox("Threshold parameters")
        self.groupThresholdLayout = QVBoxLayout()
        self.thresholdGroup.setLayout(self.groupThresholdLayout)
        self.thresholdToolLayout = QVBoxLayout()
        self.widgetThreshold = ThresholdWidget(self.viewer)
        self.thresholdToolLayout.addWidget(self.widgetThreshold)
        self.groupThresholdLayout.addLayout(self.thresholdToolLayout)

        self.ROIGroup = QGroupBox("ROI parameters")
        self.groupROILayout = QVBoxLayout()
        self.ROIGroup.setLayout(self.groupROILayout)
        self.ROIToolLayout = QVBoxLayout()
        self.widgetRejection = RoiWidget(self.viewer)
        self.ROIToolLayout.addWidget(self.widgetRejection)
        self.groupROILayout.addLayout(self.ROIToolLayout)

        layout.addWidget(self.detectionGroup)
        layout.addWidget(self.thresholdGroup)
        layout.addWidget(self.ROIGroup)
        self.setLayout(layout)


class DetectionToolTab(QWidget):
    """The main widget of the detection tool

    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.countWindows = 0
        self.detectionTool = Detection()
        self.detectionParameters = DetectionParametersWidget(self.viewer)

        self.detectedBeadsLayer = None
        self.ROILayer = None

        self.parametersButton = QPushButton()
        self.parametersButton.clicked.connect(self.openParametersWindow)
        iconPath = self.getLogoPath(get_settings().appearance.theme)
        self.parametersButton.setIcon(QIcon(str(iconPath)))
        self.parametersButton.setIconSize(QSize(35, 35))
        self.parametersButton.setFixedSize(35, 35)
        self.parametersButton.setToolTip("Open detection configurator")

        self.detectionButton = QPushButton("Visualize beads detection")
        self.detectionButton.setToolTip(
            "Get a preview of detection with current parameters"
        )
        self.detectionButton.clicked.connect(self.apply)

        self.resultsLabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.parametersButton)
        layout.addWidget(self.detectionButton)
        layout.addWidget(self.resultsLabel)
        layout.addStretch()
        self.setLayout(layout)

        self.viewer.layers.events.removed.connect(self.onLayerRemoved)

    def onLayerRemoved(self, event):
        """Manage the suppression of ROI and _centroids layers

        Args:
            event (QEvent): Informations about the triggering event
        """
        if (
            hasattr(self, "detectedBeadsLayer")
            and self.detectedBeadsLayer == event.value
        ):
            self.detectedBeadsLayer = None
        if hasattr(self, "ROILayer") and self.ROILayer == event.value:
            self.ROILayer = None

    def openParametersWindow(self):
        """A method to create parameters window and limit the maximum window number to one."""
        if self.countWindows == 0:
            self.parametersWindow = QDialog(self)
            self.parametersWindow.setWindowTitle("Detection parameters")
            self.parametersWindow.setModal(False)
            self.parametersWindow.finished.connect(
                self.onParametersWindowClosed
            )
            parametersLayout = QVBoxLayout()
            parametersLayout.addWidget(self.detectionParameters)
            self.parametersWindow.setLayout(parametersLayout)
            self.parametersWindow.show()
            self.countWindows += 1

    def onParametersWindowClosed(self, result):
        """Called when parameters window is closed to unlock the possibility to open another one and erase threshold preview.

        Args:
            result : Parameter sent by the window when closed
        """
        self.countWindows -= 1
        if self.detectionParameters.widgetThreshold.layer is not None:
            self.detectionParameters.widgetThreshold.layer.contrast_limits = (
                self.detectionParameters.widgetThreshold.oldContrastLimits
            )
            self.detectionParameters.widgetThreshold.layer.colormap = "gray"
            self.detectionParameters.widgetThreshold.layer.blending = (
                "additive"
            )

    def erase_Layers(self):
        """A method to delete all layers made by this wiget"""
        if self.ROILayer:
            self.viewer.layers.remove(self.ROILayer)
        if self.detectedBeadsLayer:
            self.viewer.layers.remove(self.detectedBeadsLayer)

    def getLogoPath(self, theme):
        """A method to automatically return the logo corresponding to the application theme.

        Args:
            theme (napari.theme): The actual theme of the napari application.

        Returns:
            Path: path to the logo corresponding to the theme.
        """
        logoDirectory = Path(__file__).parent / "res" / "drawable"
        if theme == "dark":
            return logoDirectory / "logo_dark.png"
        else:
            return logoDirectory / "logo_light.png"

    def apply(self):
        """Called when validating to launch beads detection and extraction with current parameters. It is not an analysis, only a detection preview."""
        self.detectionTool.image = self.viewer.layers.selection.active.data
        self.detectionTool._detectionTool = DetectionTool.getInstance(
            self.detectionParameters.detectionToolWidget.options.value(
                "Detection tool"
            )
        )
        self.detectionTool._detectionTool._thresholdTool = (
            Threshold.getInstance(
                self.detectionParameters.widgetThreshold.options.value(
                    "Threshold"
                )
            )
        )
        if (
            self.detectionParameters.widgetThreshold.options.value("Threshold")
            == "manual"
        ):
            self.detectionTool._detectionTool._thresholdTool._relThreshold = (
                self.detectionParameters.widgetThreshold.optionsSliders.value(
                    "threshold"
                )
                / 100
            )
        self.detectionTool._detectionTool._image = (
            self.viewer.layers.selection.active.data
        )
        self.detectionTool._detectionTool.sigma = (
            self.detectionParameters.detectionToolWidget.optionsSliders.value(
                "Sigma"
            )
        )
        if isinstance(self.detectionTool._detectionTool, PeakLocalMaxDetector):
            self.detectionTool._detectionTool.minDistance = self.detectionParameters.detectionToolWidget.optionsSliders.value(
                "Min dist"
            )
        self.detectionTool.cropFactor = (
            self.detectionParameters.widgetRejection.optionsSliders.value(
                "crop factor"
            )
        )
        self.detectionTool._thresholdIntensity = (
            self.detectionParameters.widgetRejection.optionsSliders.value(
                "threshold intensity"
            )
            / 100
        )
        self.detectionTool.beadSize = (
            self.detectionParameters.widgetRejection.options.value(
                "Theoretical bead size (µm)"
            )
        )
        self.detectionTool.rejectionDistance = (
            self.detectionParameters.widgetRejection.options.value(
                "Z axis rejection margin (µm)"
            )
        )
        kwargs = {"cropPsf": False}
        worker = create_worker(
            self.detectionTool.run,
            **kwargs,
            _progress={"desc": "Detecting beads..."},
        )
        worker.finished.connect(self.displayResult)
        worker.errored.connect(lambda: self.detectionButton.setEnabled(True))
        self.detectionButton.setEnabled(False)
        worker.start()

    def displayResult(self):
        """A method to display detected centroids and region of interest with new layers."""
        workingLayer = self.viewer.layers.selection.active
        if (
            isinstance(self.detectionTool._centroids, np.ndarray)
            and self.detectionTool._centroids.size > 0
        ):
            if self.ROILayer is None:
                self.ROILayer = self.viewer.add_shapes(
                    self.detectionTool._roisExtracted,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            else:
                self.viewer.layers.remove(self.ROILayer)
                self.ROILayer = self.viewer.add_shapes(
                    self.detectionTool._roisExtracted,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            if self.detectedBeadsLayer is None:
                self.detectedBeadsLayer = self.viewer.add_points(
                    self.detectionTool._centroids,
                    name="PSF detected",
                    face_color="red",
                    opacity=0.5,
                    size=2,
                )
            else:
                self.detectedBeadsLayer.data = self.detectionTool._centroids
            self.resultsLabel.setText(
                f"Here are the results of the detection:\n- {len(self.detectionTool._centroids)} bead(s) detected\n- {len(self.detectionTool._roisExtracted)} ROI(s) extracted"
            )
        else:
            show_warning("No PSF found or incorrect format.")
        self.detectionButton.setEnabled(True)
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.detectionTool._pixelSize
        self.viewer.layers.selection.active = workingLayer
        self.viewer.reset_view()
