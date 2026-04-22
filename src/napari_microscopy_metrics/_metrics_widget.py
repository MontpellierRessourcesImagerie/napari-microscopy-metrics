import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox

from napari_microscopy_metrics.widgets.FittingOptionWidget import (
    FittingOptionWidget,
)


class Metricstoolpage(QWidget):
    """A napari widget form for microscopy metrics parameters and results.
    It contains a FittingOptionWidget for setting fitting parameters and a label to display metrics results.
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.count_windows = 0
        self.SBR = None
        self.FWHM = []
        self.spacing = [1, 1, 1]

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.groupMetrics = QGroupBox("Metrics parameters")
        self.groupLayout = QVBoxLayout()
        self.groupMetrics.setLayout(self.groupLayout)
        self.layoutParameters = QVBoxLayout()
        self.widgetFittingChoice = FittingOptionWidget(self.viewer, self)
        self.layoutParameters.addWidget(self.widgetFittingChoice)
        self.groupLayout.addLayout(self.layoutParameters)

        self.groupResults = QGroupBox("Mean metrics measured")
        self.layoutResults = QVBoxLayout()
        self.resultsLabel = QLabel("No metric mesured yet.")
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        self.layoutResults.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.layoutResults.addWidget(self.resultsLabel)
        self.groupResults.setLayout(self.layoutResults)
        self.groupResults.setToolTip("Metrics measured at this point")
        layout.addWidget(self.groupMetrics)
        layout.addWidget(self.groupResults)
        layout.addStretch()
        self.setLayout(layout)

    def printResults(self, SBR):
        """A method to update plugin interface with the SBR of the image analyzed.
        Args:
            SBR (float): Signal to background ratio of the image.
        """
        if self.FWHM != []:
            text = f"- Signal to background ratio: {SBR:.2f}\n- FWHM Z: {self.FWHM[0]:.4f}\n- FWHM Y: {self.FWHM[1]:.4f}\n- FWHM X: {self.FWHM[2]:.4f}"
        else:
            text = f"- Signal to background ratio: {SBR:.2f}"
        self.resultsLabel.setText(text)
        self.SBR = SBR

    def printFWHM(self, FWHM):
        """A method to update plugin interface with the FWHM of the image analyzed.
        Args:
            FWHM (list): List of 3 values corresponding to FWHM in Z, Y and X of the image.
        """
        if self.SBR is not None:
            text = f"- Signal to background ratio: {self.SBR:.2f}\n- FWHM Z: {FWHM[0]:.4f}\n- FWHM Y: {FWHM[1]:.4f}\n- FWHM X: {FWHM[2]:.4f}"
        else:
            text = f"- FWHM Z: {FWHM[0]:.4f}\n- FWHM Y: {FWHM[1]:.4f}\n- FWHM X: {FWHM[2]:.4f}"
        self.resultsLabel.setText(text)
        self.FWHM = FWHM

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/results.html#napari-viewer"
        webbrowser.open(documentationPath)
