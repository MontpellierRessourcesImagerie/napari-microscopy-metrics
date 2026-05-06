import napari
import webbrowser
import numpy as np

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
from microscopy_metrics.thresholdTools.threshold_tool import Threshold

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.ThresholdDatas import ThresholdDatas


class ThresholdWidget(BaseWidget):
    """A widget allowing user to choose the Threshold he wants to apply to the image for analysis."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        self.paramsStack = None
        super().__init__(viewer)
        self.layer = None
        self.oldContrastLimits = []

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options, client=self)
        self.toolChoiceWidget = self.widget.widgets["Threshold"][1]
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
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        applybtn = self.widget.getApplyButton()
        applybtn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widget._getButtonsLayout().addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.thresholdRel.valueChanged.connect(self.updateThreshold)

    def getOptions(self):
        """A method which create entries for threshold informations and load previous analysis informations if exists.

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
            callback=self.selectedAction,
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
        if self.paramsStack is not None:
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

    def createDatas(self):
        """A method to create a ThresholdDatas object with current threshold and parameters values."""
        return ThresholdDatas(
            thresholdTool=self.options.value("Threshold"),
            thresholdRel=self.optionsSliders.value("threshold") / 100,
        )
