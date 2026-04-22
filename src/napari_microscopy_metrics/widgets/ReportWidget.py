import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox, QHBoxLayout, QSizePolicy, QVBoxLayout, QPushButton

from autooptions import Options

from napari_microscopy_metrics.widgets.BaseWidget import BaseWidget


class ReportWidget(BaseWidget):
    """A widget allowing user to setup report parameters."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__(viewer)

    def createLayout(self):
        """A method used to create the layout with options setup to previous analysis."""
        layout = QVBoxLayout()
        self.PDFCheckbox = QCheckBox("Export report as PDF")
        self.PDFCheckbox.setChecked(self.options.value("Export report as PDF"))
        layout.addWidget(self.PDFCheckbox)  
        self.CSVCheckbox = QCheckBox("Export report as CSV")
        self.CSVCheckbox.setChecked(self.options.value("Export report as CSV"))
        layout.addWidget(self.CSVCheckbox)      
        self.HTMLCheckbox = QCheckBox("Export report as HTML")
        self.HTMLCheckbox.setChecked(self.options.value("Export report as HTML"))
        layout.addWidget(self.HTMLCheckbox)
        self.ButtonLayout = QHBoxLayout()
        self.applyButton = QPushButton("Apply")
        self.applyButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.applyButton.clicked.connect(self.apply)
        self.ButtonLayout.addWidget(self.applyButton)
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedWidth(25)
        self.btnDoc.setToolTip("Go to documentation")
        self.ButtonLayout.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        layout.addLayout(self.ButtonLayout)
        self.setLayout(layout)

    @classmethod
    def getOptions(cls):
        """A class method which create entries for report parameters and load previous analysis informations if exists."""
        options = Options("Report parameters", "Select parameters for report export")
        options.addBool(name="Export report as PDF", value=True)
        options.addBool(name="Export report as CSV", value=False)
        options.addBool(name="Export report as HTML", value=False)
        options.load()
        return options

    def getSliders(self):
        pass

    def apply(self):
        self.options.setValue("Export report as PDF", self.PDFCheckbox.isChecked())
        self.options.setValue("Export report as CSV", self.CSVCheckbox.isChecked())
        self.options.setValue("Export report as HTML", self.HTMLCheckbox.isChecked())
        self.options.save()

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/results.html#napari-viewer"
        webbrowser.open(documentationPath)