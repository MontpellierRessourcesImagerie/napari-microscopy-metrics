import napari
import webbrowser
import numpy as np

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QSlider,
)
from autooptions import Options
from autooptions import OptionsWidget

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget
from napari_microscopy_metrics.InputDatas.FittingDatas import FittingDatas
from microscopy_metrics.fittingTools.fittingTool import FittingTool
from microscopy_metrics.fittingTools import Prominence


class FittingOptionWidget(BaseWidget):
    """A widget allowing user to setup fitting options for PSF detection and save them for next session."""

    def __init__(self, viewer: "napari.viewer.Viewer", parent):
        self.paramsStack = None
        self.viewer = viewer
        self.parent = parent
        super().__init__(viewer)

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer, self.options, client=self)
        self.toolChoiceWidget = self.widget.widgets["Fit type"][1]
        self.prominenceRelWidget = QWidget()
        self.prominenceRelLayout = QVBoxLayout()
        self.prominenceRelLayout.setContentsMargins(0, 0, 0, 0)
        self.prominenceRelLayout.setSpacing(2)
        self.prominenceRel = QSlider(Qt.Horizontal)
        self.prominenceRel.setRange(1, 100)
        self.prominenceRel.setValue(self.optionsSliders.value("prominence"))
        self.prominenceRelLabel = QLabel(
            "Relative prominence: " + str(self.prominenceRel.value() / 100)
        )
        self.prominenceRelLayout.addWidget(self.prominenceRelLabel)
        self.prominenceRelLayout.addWidget(self.prominenceRel)
        self.prominenceRelWidget.setLayout(self.prominenceRelLayout)
        self.emptyWidget = QWidget()
        self.emptyLayout = QVBoxLayout()
        self.emptyWidget.setLayout(self.emptyLayout)
        self.paramsStack = QStackedWidget()
        self.paramsStack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.paramsStack.addWidget(self.prominenceRelWidget)
        self.paramsStack.addWidget(self.emptyWidget)
        self.widget.mainLayout.addWidget(self.paramsStack)
        self.widget.addApplyButton(lambda: None)
        self.widget.getApplyButton().setText("Save fitting option")
        self.widget.setToolTip(
            "Select a fit tool and a threshold for rejecting bead's with a low fit quality"
        )
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
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.prominenceRel.valueChanged.connect(self.displayFWHM)

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/metrics.html#metrics-parameters"
        webbrowser.open(documentationPath)

    def selectedAction(self, value):
        """A method to display prominence slider if prominence is selected as fitting tool and hide it otherwise.
        Args:
            value (str): Value of the fitting tool choice
        """
        if self.paramsStack is not None:
            if value == "Prominence" :
                self.paramsStack.setCurrentIndex(0)
                self.displayFWHM(self.prominenceRel.value())
            else:
                self.paramsStack.setCurrentIndex(1)

    def displayFWHM(self, value):
        """A method to display mean FWHM of detected PSF with prominence fitting tool and update it when changing prominence slider value.
        Args:
            value (int): Value of the prominence slider
        """
        self.prominenceRelLabel.setText(f"Relative prominence: {value/100}")
        if "ROI" in self.viewer.layers:
            ROIs = self.viewer.layers["ROI"].data
        else:
            return
        if "PSF detected" in self.viewer.layers:
            centroids = self.viewer.layers["PSF detected"].data
        else:
            return
        if (
            not isinstance(
                self.viewer.layers.selection.active, napari.layers.Image
            )
            or self.viewer.layers.selection.active is None
        ):
            return
        image = self.viewer.layers.selection.active.data
        meanFWHM = [0.0, 0.0, 0.0]
        total = 0
        for roi in ROIs:
            center = np.mean(roi, axis=0)
            dist = np.linalg.norm(centroids - center, axis=1)
            index_min_distance = np.argmin(dist)
            prominence = Prominence()
            roi_int = roi.astype(int)
            prominence._image = image[
                ...,
                roi_int[0][1] : roi_int[2][1],
                roi_int[0][2] : roi_int[1][2],
            ]
            prominence._roi = roi
            prominence._centroid = centroids[index_min_distance]
            prominence._prominenceRel = value / 100
            prominence._spacing = self.parent.spacing
            prominence.processSingleFit(0)
            result = [0, prominence.fwhms, prominence.parameters]
            if result is None:
                continue
            total += 1
            meanFWHM = [
                meanFWHM[0] + result[1][0],
                meanFWHM[1] + result[1][1],
                meanFWHM[2] + result[1][2],
            ]
        if total > 0:
            meanFWHM = [
                meanFWHM[0] / total,
                meanFWHM[1] / total,
                meanFWHM[2] / total,
            ]
        else:
            meanFWHM = [0, 0, 0]

        self.parent.printFWHM(meanFWHM)

    def getOptions(self):
        """A class method which create entries for fitting options and load previous analysis informations if exists.
        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options("Fitting option", "set fitting option")
        options.addChoice(
            name="Fit type",
            choices=[x for x in FittingTool._fittingClasses.keys()],
            value="1D",
            callback=self.selectedAction,
        )
        options.addFloat(name="Threshold R2", value=0.95)
        options.load()
        if options.items["Fit type"]["choices"] != [
            x for x in FittingTool._fittingClasses.keys()
        ]:
            options.items["Fit type"]["choices"] = [
                x for x in FittingTool._fittingClasses.keys()
            ]
        return options

    @classmethod
    def getSliders(cls):
        """A class method which create entries for sliders values and load previous analysis informations if exists.
        Returns:
            Options: The object that contains every widget informations.
        """
        optionsSliders = Options("Sliders value", "Store value of sliders")
        optionsSliders.addInt(name="prominence", value=50)
        optionsSliders.load()
        return optionsSliders

    def createDatas(self):
        """A method to create a FittingDatas object with current fitting options values."""
        return FittingDatas(
            fitType=self.options.value("Fit type"),
            thresholdRSquared=self.options.value("Threshold R2"),
            prominenceRel=self.prominenceRel.value() / 100,
        )
