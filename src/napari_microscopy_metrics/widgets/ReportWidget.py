import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox, QVBoxLayout, QPushButton, QSlider, QLabel

from autooptions import Options, OptionsWidget

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
        self.applyButton = QPushButton("Apply")
        self.applyButton.clicked.connect(self.apply)
        layout.addWidget(self.applyButton)
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