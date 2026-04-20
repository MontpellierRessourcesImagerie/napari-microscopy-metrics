import napari
import webbrowser

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox

from napari_microscopy_metrics.widgets.ReportWidget import ReportWidget


class ReportToolPage(QWidget):
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
        self.groupReport = QGroupBox("Report parameters")
        self.groupLayout = QVBoxLayout()
        self.groupReport.setLayout(self.groupLayout)
        self.layoutParameters = QVBoxLayout()
        self.widgetReportChoices = ReportWidget(self.viewer)
        self.layoutParameters.addWidget(self.widgetReportChoices)
        self.btnDoc = QPushButton("?")
        self.btnDoc.pressed.connect(self.openDocumentation)
        self.btnDoc.setFixedSize(24, 24)
        self.btnDoc.setToolTip("Go to documentation")
        self.layoutParameters.addWidget(self.btnDoc, alignment=Qt.AlignRight)
        self.groupLayout.addLayout(self.layoutParameters)

        layout.addWidget(self.groupReport)
        layout.addStretch()
        self.setLayout(layout)

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/results.html#napari-viewer"
        webbrowser.open(documentationPath)

    def getListReports(self):
        """A method to get the list of report to export based on user choices in the widget interface."""
        listReports = []
        if self.widgetReportChoices.options.value("Export report as PDF"):
            listReports.append("PDF")
        if self.widgetReportChoices.options.value("Export report as CSV"):
            listReports.append("CSV")
        if self.widgetReportChoices.options.value("Export report as HTML"):
            listReports.append("HTML")
        return listReports
