"""
This module contains a QWidget class for performing PSF analysis.

"""

from typing import TYPE_CHECKING, Optional
import types
import napari
from napari.qt.threading import thread_worker,create_worker
from napari.utils import progress
from magicgui import magic_factory
from magicgui.widgets import CheckBox, Container, create_widget
from qtpy.QtCore import Qt, QSize, Signal, QObject, QThread
from qtpy.QtWidgets import *
from napari_microscopy_metrics._detection_tool_widget import DetectionToolTab
from napari_microscopy_metrics._acquisition_widget import *
from napari_microscopy_metrics._metrics_widget import *
from microscopy_metrics.detection import Detection
from microscopy_metrics.detection_tool import DetectionTool,PeakLocalMaxDetector
from microscopy_metrics.metrics import Metrics
from microscopy_metrics.threshold_tool import Threshold
from microscopy_metrics.fitting import Fitting
from microscopy_metrics.report_generator import ReportGenerator
import webbrowser
import numpy as np

class Microscopy_Metrics_QWidget(QWidget):
    """
    Main Widget of the plugin
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.analysisData = []
        self.DetectionTool = Detection()
        self.MetricTool = Metrics()
        self.FittingTool = Fitting()
        self.reportGenerator = ReportGenerator()
        self.parametersDetection = {}
        self.parametersAcquisition = {}
        self.centroidsLayer = None
        self.roisLayer = None
        self.filteredBeads = None
        self.workingLayer = None
        self.outputDir = None
        self.meanSBR = 0
        self.selectedShape = 0
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.setDocumentMode(True)
        self.acquisitionToolPage = AcquisitionToolPage(self.viewer)
        self.acquisitionToolPage.widgetPxS.signal.scaleUpdate.connect(self.updateScaleDetection)
        self.acquisitionToolPage.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.tab.addTab(self.acquisitionToolPage, "Acquisition parameters")
        self.detectionToolPage = DetectionToolTab(self.viewer)
        self.detectionToolPage.detectionTool._pixelSize = [
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size Z"),
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size Y"),
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size X"),
            ]
        self.detectionToolPage.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.tab.addTab(self.detectionToolPage, "Detection parameters")
        self.metricsToolPage = Metricstoolpage(self.viewer)
        self.metricsToolPage.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.tab.addTab(self.metricsToolPage, "Metrics parameters")
        self.runButton = QPushButton("Run analysis")
        self.runButton.setStyleSheet("background-color : green")
        self.runButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.docButton = QPushButton("Documentation")
        self.docButton.setStyleSheet("background-color : blue")
        self.docButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.runButton)
        self.layout().addWidget(self.docButton)
        self.runButton.pressed.connect(self.startProcessing)
        self.docButton.pressed.connect(self.openDocumentation)
        self.viewer.mouse_double_click_callbacks.append(
            self.onMouseDoubleClick
        )

    def startProcessing(self):
        """Initialize layers and start thread for analysis"""
        self.workingLayer = self.viewer.layers.selection.active
        self.analysisData = []
        if self.workingLayer is None or not isinstance(
            self.workingLayer, napari.layers.Image
        ):
            show_error("Please, select a valid layer of type Image")
            return
        self.detectionToolPage.erase_Layers()
        self.runButton.setEnabled(False)
        self.apply_detect_psf()

    def apply_detect_psf(self):
        """Update DetectionTool with new values and start a new worker for detection"""
        image = self.workingLayer.data
        self.DetectionTool._detectionTool = DetectionTool.getInstance(self.detectionToolPage.detectionParameters.detectionToolWidget.options.value("Detection tool"))
        self.DetectionTool._detectionTool._thresholdTool = Threshold.getInstance(self.detectionToolPage.detectionParameters.widgetThreshold.options.value("Threshold"))
        if self.detectionToolPage.detectionParameters.widgetThreshold.options.value("Threshold") == "manual":
            self.DetectionTool._detectionTool._thresholdTool._relThreshold = self.detectionToolPage.detectionParameters.widgetThreshold.optionsSliders.value("threshold") / 100
        self.DetectionTool._detectionTool._image = image
        self.DetectionTool._detectionTool.sigma = self.detectionToolPage.detectionParameters.detectionToolWidget.optionsSliders.value("Sigma")
        if isinstance(self.DetectionTool._detectionTool, PeakLocalMaxDetector):
            self.DetectionTool._detectionTool.minDistance = self.detectionToolPage.detectionParameters.detectionToolWidget.optionsSliders.value("Min dist")
        self.DetectionTool._image = image
        self.DetectionTool._sigma = self.detectionToolPage.detectionParameters.detectionToolWidget.optionsSliders.value("Sigma")
        self.DetectionTool._cropFactor = self.detectionToolPage.detectionParameters.widgetRejection.optionsSliders.value("crop factor")
        self.DetectionTool._beadSize = self.detectionToolPage.detectionParameters.widgetRejection.options.value("Theoretical bead size (µm)")
        self.DetectionTool._rejectionDistance = self.detectionToolPage.detectionParameters.widgetRejection.options.value("Z axis rejection margin (µm)")
        self.DetectionTool._pixelSize = np.array(
            [
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size Z"),
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size Y"),
                self.acquisitionToolPage.widgetPxS.options.value("Pixel size X"),
            ]
        )
        self.outputDir = os.path.expanduser("~/")
        if (
            self.workingLayer is not None
            and hasattr(self.workingLayer, "source")
            and self.workingLayer.source.path
        ):
            imagePath = self.workingLayer.source.path
            self.outputDir = os.path.dirname(imagePath)
        args = [self.outputDir]
        worker = create_worker(
            self.DetectionTool.run,
            *args,
            _progress={"desc": "Detecting beads..."},
        )
        worker.finished.connect(self.detectFinished)
        worker.errored.connect(self.onReportFinished)
        worker.yielded.connect(
            lambda value: worker.pbar.set_description(value["desc"])
        )
        worker.start()

    def detectFinished(self):
        """Function to update napari with new layers displaying bead detection

        Raises:
            ValueError: Error raised when the bead detection did not worked or if there are no beads in the image
        """
        self.filteredBeads = self.DetectionTool._centroids
        if (
            isinstance(self.filteredBeads, np.ndarray)
            and self.filteredBeads.size > 0
        ):
            rois = self.DetectionTool._roisExtracted
            centroidsROI = self.DetectionTool._listIdCentroidsRetained
            for x, id in enumerate(centroidsROI):
                data = {"id": id, "ROI": rois[x]}
                self.analysisData.append(data)
        if len(self.DetectionTool._cropped) == 0:
            raise ValueError("There are no _cropped PSF !")
        for i in range(len(self.DetectionTool._cropped)):
            self.analysisData[i]["_cropped"] = self.DetectionTool._cropped[i]
        self.displayLayers()
        self.applyPrefittingMetrics()

    def applyPrefittingMetrics(self):
        """Function to update MetricTool and start a worker for prefitting metrics calculation"""
        physicalPixel = [
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Z"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Y"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size X"),
        ]
        self.MetricTool.image = self.workingLayer.data
        self.MetricTool.images = [
            entry["_cropped"] for entry in self.analysisData
        ]
        self.MetricTool.ringInnerDistance = self.detectionToolPage.detectionParameters.widgetRejection.options.value("Inner annulus distance to bead (µm)")
        self.MetricTool.ringThickness = self.detectionToolPage.detectionParameters.widgetRejection.options.value("Annulus thickness (µm)")
        self.MetricTool.theoreticalResolutionTool = TheoreticalResolution.getInstance(self.acquisitionToolPage.widgetMicroChoice.options.value("Microscope type"))
        self.MetricTool.theoreticalResolutionTool.numericalAperture = self.acquisitionToolPage.widgetMicroChoice.options.value("Numerical aperture")
        self.MetricTool.theoreticalResolutionTool.emissionWavelength = self.acquisitionToolPage.widgetMicroChoice.options.value("Emission wavelength")
        self.MetricTool.theoreticalResolutionTool.refractiveIndex = self.acquisitionToolPage.widgetMicroChoice.options.value("Refraction index")
        self.MetricTool.pixelSize = np.array(physicalPixel)
        worker = create_worker(
            self.MetricTool.runPrefittingMetrics,
            _progress={"desc": "Metrics calculation..."},
        )
        worker.finished.connect(self.prefittingFinished)
        worker.errored.connect(self.onReportFinished)
        worker.start()

    def prefittingFinished(self):
        """Function to update napari display with prefitting metrics results

        Raises:
            ValueError: Raised when an error occurred in the signal to background ratio computation
        """
        if len(self.MetricTool.SBR) != len(self.analysisData):
            raise ValueError("Problem with SBR calculation")
        for x, sbr in enumerate(self.MetricTool.SBR):
            self.analysisData[x]["SBR"] = sbr
        self.metricsToolPage.printResults(self.MetricTool.meanSBR)
        self.meanSBR = self.MetricTool.meanSBR
        self.applyFitting()

    def applyFitting(self):
        """Function to update FittingTool and start a worker for Gaussian fitting"""
        self.FittingTool.images = [
            entry["_cropped"] for entry in self.analysisData
        ]
        centroidsIdx = [entry["id"] for entry in self.analysisData]
        self.FittingTool._centroids = [
            self.filteredBeads[i] for i in centroidsIdx
        ]
        self.FittingTool.spacing = [
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Z"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Y"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size X"),
        ]
        self.FittingTool.rois = [entry["ROI"] for entry in self.analysisData]
        self.FittingTool.outputDir = self.outputDir
        self.FittingTool.fitType = self.metricsToolPage.widgetFittingChoice.options.value("Fit type")

        worker = create_worker(
            self.FittingTool.computeFitting,
            _progress={"desc": "Gaussian fitting..."},
        )
        worker.finished.connect(self.onFinished)
        worker.errored.connect(self.onReportFinished)
        worker.start()

    def onFinished(self):
        """Function to update result collection and start a worker for report generation"""
        for i, result in enumerate(self.FittingTool.results):
            self.analysisData[result[0]]["FWHM"] = []
            self.analysisData[result[0]]["uncertainty"] = []
            self.analysisData[result[0]]["determination"] = []
            self.analysisData[result[0]]["FWHM"] = result[1]
            self.MetricTool.FWHM = result[1]
            self.MetricTool.lateralAsymmetryRatio()
            self.analysisData[result[0]]["LAR"] = self.MetricTool.LAR
            self.MetricTool.sphericityRatio()
            self.analysisData[result[0]][
                "sphericity"
            ] = self.MetricTool.sphericity
            self.analysisData[result[0]]["uncertainty"] = result[2]
            self.analysisData[result[0]]["determination"] = result[3]
        worker = create_worker(
            self.generateReport, _progress={"desc": "Generating report..."}
        )
        worker.finished.connect(self.onReportFinished)
        worker.errored.connect(self.onReportFinished)
        worker.yielded.connect(
            lambda value: worker.pbar.set_description(value["desc"])
        )
        worker.start()

    def generateReport(self):
        """Function for generating PDF,csv and HTML reports

        Yields:
            string : used to change the description of the napari progress bar
        """
        # Extracting ROIs and _cropped layers from analysisData
        rois = [entry["ROI"] for entry in self.analysisData]
        croppedLayers = [entry["_cropped"] for entry in self.analysisData]
        outputDir = os.path.expanduser("~/")
        defaultPath = os.path.expanduser("~/PSF_analysis_result.pdf")
        imagePath = outputDir
        if (
            self.workingLayer is not None
            and hasattr(self.workingLayer, "source")
            and self.workingLayer.source.path
        ):
            imagePath = self.workingLayer.source.path
            outputDir = os.path.dirname(imagePath)
            outputPath = os.path.join(
                outputDir, f"{self.workingLayer.name}_analysis_result.pdf"
            )
            outputCSVPath = os.path.join(
                outputDir, f"{self.workingLayer.name}_analysis_result.csv"
            )
        else:
            outputPath = defaultPath
        self.reportGenerator.outputDir = outputDir
        self.reportGenerator.outputPath = outputPath
        self.reportGenerator.analysisData = self.analysisData
        originalDict = self.acquisitionToolPage.widgetPxS.options.items | self.acquisitionToolPage.widgetMicroChoice.options.items
        simplifiedDict = {key: subDict['value'] for key, subDict in originalDict.items()}
        self.reportGenerator._imageShape = self.workingLayer.data.shape
        self.reportGenerator.parametersAcquisition = simplifiedDict
        originalDict = self.detectionToolPage.detectionParameters.detectionToolWidget.options.items | self.detectionToolPage.detectionParameters.detectionToolWidget.optionsSliders.items | self.detectionToolPage.detectionParameters.widgetThreshold.options.items | self.detectionToolPage.detectionParameters.widgetThreshold.optionsSliders.items | self.detectionToolPage.detectionParameters.widgetRejection.options.items | self.detectionToolPage.detectionParameters.widgetRejection.optionsSliders.items
        simplifiedDict = {key: subDict['value'] for key, subDict in originalDict.items()}
        self.reportGenerator.parametersDetection = simplifiedDict
        self.reportGenerator.filteredBeads = self.filteredBeads
        self.reportGenerator.meanSBR = self.meanSBR
        self.reportGenerator.theoreticalResolution = self.MetricTool.theoreticalResolution
        yield {"desc": "Generating pdf..."}
        self.reportGenerator.generatePDFReport(imagePath)
        yield {"desc": "Generating html..."}
        self.reportGenerator.generateHTMLReport()
        yield {"desc": "Generating csv..."}
        self.reportGenerator.generateCSVReport(outputCSVPath)

    def onReportFinished(self):
        """Called to Enable the button to run analysis"""
        self.runButton.setEnabled(True)

    def openBrowser(self):
        """Open html page report of the selected shape
        """
        activePath = self.getActivePath(index=self.selectedShape)
        activePath = os.path.join(activePath, "PSF_analysis_result.html")
        webbrowser.open(activePath)

    def openDocumentation(self):
        """Open index page of documentation
        """
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/index.html"
        webbrowser.open(documentationPath)


    def onMouseDoubleClick(self, layer, event):
        """Function to display HTML report corresponding to the bead selected by user.

        Args:
            layer : Information about the layer clicked sent with the signal
            event : Information relative to the event sent with the signal
        """

        clickPos = self.viewer.cursor.position / self.workingLayer.scale

        if self.roisLayer is None:
            return

        for i, shape in enumerate(self.roisLayer.data):
            yCoords = [point[1] for point in shape]
            xCoords = [point[2] for point in shape]
            xMin, xMax = min(xCoords), max(xCoords)
            yMin, yMax = min(yCoords), max(yCoords)

            if (
                clickPos[1] >= yMin
                and clickPos[1] <= yMax
                and clickPos[2] >= xMin
                and clickPos[2] <= xMax
            ):
                self.selectedShape = i
                self.openBrowser()
                event.handled = True
                return

    def getActivePath(self, index):
        """
        Args:
            index (int): Bead ID corresponding to it's position in the list

        Returns:
            Path: Folder's path found (or created) for the selected bead
        """
        activePath = os.path.join(self.outputDir, f"bead_{index}")
        if not os.path.exists(activePath):
            os.makedirs(activePath)
        return activePath

    def displayLayers(self):
        """Add layers for detected beads and extracted ROIs
        Update scale and units of the napari viewer"""
        rois = [entry["ROI"] for entry in self.analysisData]
        if (
            isinstance(self.filteredBeads, np.ndarray)
            and self.filteredBeads.size > 0
        ):
            if self.centroidsLayer is None:
                self.centroidsLayer = self.viewer.add_points(
                    self.filteredBeads,
                    name="PSF detected",
                    face_color="red",
                    opacity=0.5,
                    size=2,
                )
            else:
                self.centroidsLayer.data = self.filteredBeads
            self.detectionToolPage.resultsLabel.setText(
                f"Here are the results of the detection:\n- {len(self.filteredBeads)} bead(s) detected\n- {len(rois)} ROI(s) extracted"
            )
        else:
            show_warning("No PSF found or incorrect format.")
        if len(rois) > 0:
            features = {"label": [f"bead_{i}" for i in range(len(rois))]}
            text = {
                "string": "{label}",
                "anchor": "upper_left",
                "translation": [5, -5, 5],
                "size": 8,
                "color": "green",
            }
            if self.roisLayer is None:
                self.roisLayer = self.viewer.add_shapes(
                    rois,
                    features=features,
                    text=text,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            else:
                self.viewer.layers.remove(self.roisLayer)
                self.roisLayer = None
                self.roisLayer = self.viewer.add_shapes(
                    rois,
                    features=features,
                    text=text,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
        self.viewer.layers.selection.active = self.workingLayer
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixelSize
        self.viewer.reset_view()

    def updateScaleDetection(self, scale):
        """Update detectionToolPage when pixel scale is changed in acquisitionToolPage

        Args:
            scale (List): List of pixel scale for each axis
        """
        self.detectionToolPage.detectionTool._pixelSize = scale
