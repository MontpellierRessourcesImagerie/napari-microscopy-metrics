"""
This module contains a napari widgets form for microscope acquisition parameters
"""

from pathlib import Path
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
from microscopy_metrics.fitting import FittingTool

class FittingOptionWidget(QWidget):
    """A widget alowing user to select the fitting method he wants to use to estimate full-width half maximum."""

    def __init__(self,viewer:"napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        self.widget = OptionsWidget(self.viewer,self.options)
        self.widget.addApplyButton(lambda : None)
        self.widget.mainLayout.itemAt(1).widget().setText("Save fitting option")
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for fitting choice and load previous analysis informations if exists.

        Returns:
            Options: The object that contains every widget informations.
        """
        options = Options("Fitting option","set fitting option")
        options.addChoice(name="Fit type", choices=[x for x in FittingTool._fittingClasses.keys()], value="1D")
        options.load()
        if options.items["Fit type"]['choices'] != [x for x in FittingTool._fittingClasses.keys()] :
            options.items["Fit type"]['choices'] = [x for x in FittingTool._fittingClasses.keys()]
        return options

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

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.groupMetrics = QGroupBox("Metrics parameters")
        self.groupLayout = QVBoxLayout()
        self.groupMetrics.setLayout(self.groupLayout)
        self.layoutParameters = QVBoxLayout()
        self.widgetFittingChoice = FittingOptionWidget(self.viewer)
        self.layoutParameters.addWidget(self.widgetFittingChoice)
        self.groupLayout.addLayout(self.layoutParameters)

        self.groupResults = QGroupBox("Mean metrics measured")
        self.layoutResults = QVBoxLayout()
        self.resultsLabel = QLabel("No metric mesured yet.")
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
        text = f"- Signal to background ratio: {SBR:.2f}"
        self.resultsLabel.setText(text)
