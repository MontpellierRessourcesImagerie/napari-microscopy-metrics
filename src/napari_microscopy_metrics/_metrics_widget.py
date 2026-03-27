"""
This module contains a napari widgets form for microscope acquisition parameters
"""

from pathlib import Path
import numpy as np
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
from microscopy_metrics.fitting import FittingTool,Prominence
import webbrowser


class FittingOptionWidget(QWidget):
    """A widget alowing user to select the fitting method he wants to use to estimate full-width half maximum."""

    def __init__(self,viewer:"napari.viewer.Viewer",parent):
        super().__init__()
        self.viewer = viewer
        self.parent = parent
        self.options = self.getOptions()
        self.optionsSliders = self.getSliders()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer,self.options)
        self.toolChoiceWidget = self.widget.mainLayout.itemAt(0).itemAt(1).widget()
        self.toolChoiceWidget.currentTextChanged.connect(self.selectedAction)
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
        self.widget.addApplyButton(lambda : None)
        self.widget.mainLayout.itemAt(3).widget().setText("Save fitting option")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24,24)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        layout.addWidget(self.btnDoc,alignment=Qt.AlignRight)
        self.setLayout(layout)
        self.selectedAction(self.toolChoiceWidget.currentText())
        self.prominenceRel.valueChanged.connect(self.displayFWHM)

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/metrics.html#metrics-parameters"
        webbrowser.open(documentationPath)

    def selectedAction(self, value):
        """Update the display for selected fit.

        Args:
            value (string): label of the selection.
        """
        if value == "Prominence":
            self.paramsStack.setCurrentIndex(0)
        else :
            self.paramsStack.setCurrentIndex(1)

    def displayFWHM(self,value):
        """A method to display mean FWHM of image if ROI are already extracted and prominence is selected. 

        Args:
            value (int): Value of the relative prominence
        """
        self.prominenceRelLabel.setText(f"Relative prominence: {value/100}")
        if "ROI" in self.viewer.layers : 
            ROIs = self.viewer.layers["ROI"].data
        else :
            return
        if "PSF detected" in self.viewer.layers:
            centroids = self.viewer.layers["PSF detected"].data
        else : 
            return
        if not isinstance(self.viewer.layers.selection.active,napari.layers.Image) or self.viewer.layers.selection.active is None:
            return
        image = self.viewer.layers.selection.active.data
        centers_ROIs = []
        meanFWHM = [0.0,0.0,0.0]
        total = 0
        for roi in ROIs:
            center = np.mean(roi, axis=0)
            dist = np.linalg.norm(centroids - center, axis=1)
            index_min_distance = np.argmin(dist)
            prominence = Prominence()
            roi_int = roi.astype(int)
            prominence._image = data = image[..., roi_int[0][1] : roi_int[2][1], roi_int[0][2] : roi_int[1][2]]
            prominence._roi = roi
            prominence._centroid = centroids[index_min_distance]
            prominence._prominenceRel = value / 100
            prominence._spacing = self.parent.spacing
            result = prominence.processSingleFit(0)
            if result is None :
                continue
            total += 1
            meanFWHM = [meanFWHM[0]+result[1][0], meanFWHM[1]+result[1][1], meanFWHM[2]+result[1][2]]
        if total > 0:
            meanFWHM = [meanFWHM[0]/total, meanFWHM[1]/total, meanFWHM[2]/total]
        else : 
            meanFWHM = [0,0,0]
        
        self.parent.printFWHM(meanFWHM)




    @classmethod
    def getOptions(cls):
        """A class method which create entries for fitting choice and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options("Fitting option","set fitting option")
        options.addChoice(name="Fit type", choices=[x for x in FittingTool._fittingClasses.keys()], value="1D")
        options.addFloat(name="Threshold R2", value=0.95)
        options.load()
        if options.items["Fit type"]['choices'] != [x for x in FittingTool._fittingClasses.keys()] :
            options.items["Fit type"]['choices'] = [x for x in FittingTool._fittingClasses.keys()]
        return options

    def getSliders(self):
        """A method which create entries for prominence sliders informations and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        optionsSliders = Options("Sliders value", "Store value of sliders")
        optionsSliders.addInt(name="prominence", value=50)
        optionsSliders.load()
        return optionsSliders

class Metricstoolpage(QWidget):
    """The main widget for microscope metrics parameters

    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.count_windows = 0
        self.SBR = None
        self.FWHM = []
        self.spacing = [1,1,1]

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.groupMetrics = QGroupBox("Metrics parameters")
        self.groupLayout = QVBoxLayout()
        self.groupMetrics.setLayout(self.groupLayout)
        self.layoutParameters = QVBoxLayout()
        self.widgetFittingChoice = FittingOptionWidget(self.viewer,self)
        self.layoutParameters.addWidget(self.widgetFittingChoice)
        self.groupLayout.addLayout(self.layoutParameters)

        self.groupResults = QGroupBox("Mean metrics measured")
        self.layoutResults = QVBoxLayout()
        self.resultsLabel = QLabel("No metric mesured yet.")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24,24)
        self.layoutResults.addWidget(self.btnDoc,alignment=Qt.AlignRight)
        self.layoutResults.addWidget(self.resultsLabel)
        self.groupResults.setLayout(self.layoutResults)
        layout.addWidget(self.groupMetrics)
        layout.addWidget(self.groupResults)
        layout.addStretch()
        self.setLayout(layout)

    def printResults(self, SBR):
        """A method to update plugin interface with the mean SBR of the image analyzed.

        Args:
            SBR (float): Mean signal to background ratio of the image.
        """
        if self.FWHM != []:
            text = f"- Signal to background ratio: {SBR:.2f}\n- FWHM Z: {self.FWHM[0]:.4f}\n- FWHM Y: {self.FWHM[1]:.4f}\n- FWHM X: {self.FWHM[2]:.4f}"
        else :
            text = f"- Signal to background ratio: {SBR:.2f}"
        self.resultsLabel.setText(text)
        self.SBR = SBR

    def printFWHM(self, FWHM):
        """A method to update plugin interface with the mean FWHM of the image analyzed.

        Args:
            FWHM (float): Mean FWHM of the image.
        """
        if self.SBR is not None :
            text = f"- Signal to background ratio: {self.SBR:.2f}\n- FWHM Z: {FWHM[0]:.4f}\n- FWHM Y: {FWHM[1]:.4f}\n- FWHM X: {FWHM[2]:.4f}"
        else :
            text = f"- FWHM Z: {FWHM[0]:.4f}\n- FWHM Y: {FWHM[1]:.4f}\n- FWHM X: {FWHM[2]:.4f}"
        self.resultsLabel.setText(text)
        self.FWHM = FWHM

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/results.html#napari-viewer"
        webbrowser.open(documentationPath)
