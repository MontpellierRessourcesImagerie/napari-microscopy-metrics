"""
This module contains a QWidget class for performing PSF analysis.

"""

import os
import napari
import webbrowser
import numpy as np
import skimage.filters

from skimage.measure import marching_cubes
from napari.qt.threading import create_worker
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QTabWidget,
)
from napari.utils.notifications import show_info, show_warning, show_error

from microscopy_metrics.fitting import Fitting
from microscopy_metrics.metrics import Metrics
from microscopy_metrics.detection import Detection
from microscopy_metrics.report_generator import ReportGenerator
from microscopy_metrics.thresholdTools.threshold_tool import Threshold
from microscopy_metrics.detectionTools.detection_tool import DetectionTool
from microscopy_metrics.detectionTools.peakLocalMax import PeakLocalMaxDetector
from microscopy_metrics.resolutionTools.theoretical_resolution import (
    TheoreticalResolution,
)
from microscopy_metrics.scripts.evaluate_fitting import (
    generateRandomBornoWolfPSF,
    PSF_SIZE,
)

from napari_microscopy_metrics._metrics_widget import Metricstoolpage
from napari_microscopy_metrics._detection_tool_widget import DetectionToolTab
from napari_microscopy_metrics._acquisition_widget import AcquisitionToolPage


class Microscopy_Metrics_QWidget(QWidget):
    """A QWidget gathering all the tools for PSF analysis and allowing user to run the whole analysis and generate reports."""

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
        self.acquisitionToolPage.widgetPxS.signal.scaleUpdate.connect(
            self.updateScaleDetection
        )
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
        self.metricsToolPage.spacing = [
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Z"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size Y"),
            self.acquisitionToolPage.widgetPxS.options.value("Pixel size X"),
        ]
        self.tab.addTab(self.metricsToolPage, "Metrics parameters")
        self.runButton = QPushButton("Run analysis")
        self.runButton.setStyleSheet("background-color : green")
        self.runButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.docButton = QPushButton("Documentation")
        self.docButton.setStyleSheet("background-color : blue")
        self.docButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.genButton = QPushButton("Generate random PSF")
        self.genButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.meshButton = QPushButton("Generate 3D mesh")
        self.meshButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.genButton)
        self.layout().addWidget(self.runButton)
        self.layout().addWidget(self.docButton)
        self.layout().addWidget(self.meshButton)
        self.runButton.pressed.connect(self.startProcessing)
        self.docButton.pressed.connect(self.openDocumentation)
        self.genButton.pressed.connect(self.generateRandomPSF)
        self.meshButton.pressed.connect(self.generateMesh)
        self.viewer.mouse_double_click_callbacks.append(
            self.onMouseDoubleClick
        )

    def startProcessing(self):
        """Function called when pressing the button to run analysis. It check if the selected layer is valid and launch the bead detection process."""
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
        """Function to update DetectionTool and start a worker for bead detection"""
        image = self.workingLayer.data
        parametersDetection = self.detectionToolPage.detectionParameters.detectionToolWidget.createDatas()
        parametersDetection.sendDatas(self.DetectionTool)
        self.DetectionTool._image = image
        parametersThreshold = self.detectionToolPage.detectionParameters.widgetThreshold.createDatas()
        parametersThreshold.sendDatas(self.DetectionTool._detectionTool)
        parametersROI = self.detectionToolPage.detectionParameters.widgetRejection.createDatas()
        parametersROI.sendDatas(self.DetectionTool)
        parametersPixelSize = self.acquisitionToolPage.widgetPxS.createDatas()
        parametersPixelSize.sendDatas(self.DetectionTool)
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
        """Function to update result collection after bead detection and start prefitting metrics calculation
        Raises:
            ValueError: Raised when there is a problem with the signal to background ratio calculation
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
        self.MetricTool.image = self.workingLayer.data
        self.MetricTool.images = [
            entry["_cropped"] for entry in self.analysisData
        ]
        parametersPixelSize = self.acquisitionToolPage.widgetPxS.createDatas()
        parametersPixelSize.sendDatas(self.MetricTool)
        parametersROI = self.detectionToolPage.detectionParameters.widgetRejection.createDatas()
        parametersROI.sendDatas(self.MetricTool)
        parametersMicroscope = self.acquisitionToolPage.widgetMicroChoice.createDatas()
        parametersMicroscope.sendDatas(self.MetricTool)
        worker = create_worker(
            self.MetricTool.runPrefittingMetrics,
            _progress={"desc": "Metrics calculation..."},
        )
        worker.finished.connect(self.prefittingFinished)
        worker.errored.connect(self.onReportFinished)
        worker.start()

    def prefittingFinished(self):
        """Function to update result collection after prefitting metrics calculation and start fitting process
        Raises:
            ValueError: Raised when there is a problem with the signal to background ratio calculation
        """
        if len(self.MetricTool.SBR) != len(self.analysisData):
            raise ValueError("Problem with SBR calculation")
        for x, sbr in enumerate(self.MetricTool.SBR):
            self.analysisData[x]["SBR"] = sbr
        self.metricsToolPage.printResults(self.MetricTool.meanSBR)
        self.meanSBR = self.MetricTool.meanSBR
        self.applyFitting()

    def applyFitting(self):
        """Function to update FittingTool and start a worker for fitting process"""
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
        
        parametersFitting = self.metricsToolPage.widgetFittingChoice.createDatas()
        parametersFitting.sendDatas(self.FittingTool)

        worker = create_worker(
            self.FittingTool.computeFitting,
            _progress={"desc": "Gaussian fitting..."},
        )
        worker.finished.connect(self.onFinished)
        worker.errored.connect(self.onReportFinished)
        worker.start()

    def onFinished(self):
        """Function to update result collection after fitting process and start report generation
        Raises:
            ValueError: Raised when there is a problem with the fitting results collection
        """
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
        if len(self.FittingTool.results) == len(self.FittingTool.retainedId):
            tmp = []
            for i in self.FittingTool.retainedId:
                tmp.append(self.analysisData[i])
            self.analysisData = tmp
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
        """Function to generate report with ReportGenerator using the results of the analysis and information setup by user in the widget.
        Raises:
            ValueError: Raised when there is a problem with the report generation (missing information, problem with the data collected, etc.)
        yield:
            dict: A dictionary containing the description of the current step of the report generation to update the progress bar description
        """
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
        originalDict = (
            self.acquisitionToolPage.widgetPxS.options.items
            | self.acquisitionToolPage.widgetMicroChoice.options.items
        )
        simplifiedDict = {
            key: subDict["value"] for key, subDict in originalDict.items()
        }
        self.reportGenerator._imageShape = self.workingLayer.data.shape
        self.reportGenerator.parametersAcquisition = simplifiedDict
        originalDict = (
            self.detectionToolPage.detectionParameters.detectionToolWidget.options.items
            | self.detectionToolPage.detectionParameters.detectionToolWidget.optionsSliders.items
            | self.detectionToolPage.detectionParameters.widgetThreshold.options.items
            | self.detectionToolPage.detectionParameters.widgetThreshold.optionsSliders.items
            | self.detectionToolPage.detectionParameters.widgetRejection.options.items
            | self.detectionToolPage.detectionParameters.widgetRejection.optionsSliders.items
        )
        simplifiedDict = {
            key: subDict["value"] for key, subDict in originalDict.items()
        }
        self.reportGenerator.parametersDetection = simplifiedDict
        self.reportGenerator.filteredBeads = self.filteredBeads
        self.reportGenerator.meanSBR = self.meanSBR
        self.reportGenerator.theoreticalResolution = (
            self.MetricTool.theoreticalResolution
        )
        yield {"desc": "Generating pdf..."}
        self.reportGenerator.generatePDFReport(imagePath)
        yield {"desc": "Generating html..."}
        self.reportGenerator.generateHTMLReport()
        yield {"desc": "Generating csv..."}
        self.reportGenerator.generateCSVReport(outputCSVPath)

    def onReportFinished(self):
        """Function to display a message when the report generation is finished or if there is an error during the process and re-enable the run button"""
        show_info(
            "Report generation finished! You can find the report in the same folder as your image with the name <image_name>_analysis_result.pdf"
        )
        self.runButton.setEnabled(True)

    def openBrowser(self):
        """Function to open the HTML report corresponding to the bead selected by user in napari viewer when double-clicking on it
        Raises:
            ValueError: Raised when there is a problem with the path to the report corresponding to the bead selected (missing report, problem with the path, etc.)
        """
        activePath = self.getActivePath(index=self.selectedShape)
        activePath = os.path.join(activePath, "PSF_analysis_result.html")
        webbrowser.open(activePath)

    def openDocumentation(self):
        """A method to open the documentation webPage relative to this widget"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/index.html"
        webbrowser.open(documentationPath)

    def onMouseDoubleClick(self, layer, event):
        """Function to select the bead corresponding to the position of the double click and open the corresponding report in a web browser
        Args:
            layer (Layer): The napari layer on which the double click event happened
            event (MouseEvent): The mouse event corresponding to the double click
        Raises:
            ValueError: Raised when there is a problem with the position of the click or if there is no bead corresponding to the click position
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
        """Function to get the path to the report corresponding to the bead selected by user in napari viewer
        Args:
            index (int): The index of the bead selected corresponding to the index of the ROI in the list of ROIs extracted during the detection step
        Raises:
            ValueError: Raised when there is a problem with the path to the report corresponding to the bead selected (missing report, problem with the path, etc.)
        Returns:
            str: The path to the report corresponding to the bead selected
        """
        activePath = os.path.join(self.outputDir, f"bead_{index}")
        if not os.path.exists(activePath):
            os.makedirs(activePath)
        return activePath

    def displayLayers(self):
        """Function to display the layers corresponding to the results of the detection (centroids and ROIs) in napari viewer and update the scale of all layers according to pixel size setup by user in acquisitionToolPage
        Raises:
            ValueError: Raised when there is a problem with the data of the beads detected or the ROIs extracted (missing data, incorrect format, etc.)
        """
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
        """Function to update the scale of the layers in napari viewer and the pixel size in DetectionTool and MetricTool when user update the pixel size in acquisitionToolPage
        Args:
            scale (list): The new pixel size to apply corresponding to the value setup by user in acquisitionToolPage
        Raises:
            ValueError: Raised when there is a problem with the scale provided (incorrect format, missing value, etc.)
        """
        self.detectionToolPage.detectionTool._pixelSize = scale
        self.metricsToolPage.spacing = scale

    def generateRandomPSF(self):
        """Function to generate a random PSF and display it in the napari viewer
        Raises:
            ValueError: Raised when there is a problem with the generation of the random PSF
        """
        seed = np.random.randint(0, 1000000)
        psf, _, _ = generateRandomBornoWolfPSF(seed=seed)
        psf = psf.reshape((PSF_SIZE, PSF_SIZE, PSF_SIZE))
        self.viewer.add_image(psf, name=f"Random PSF (seed: {seed})")

    def getContourspoints(self,psf):
        points = []
        for i in range(psf.shape[0]):
            slice_2d = psf[i]
            level = Threshold().getInstance("otsu")
            level = level.getThreshold(psf)
            contours = skimage.measure.find_contours(slice_2d,level = level)
            for contour in contours:
                for point in contour :
                    points.append([i,point[0],point[1]])
        return np.array(points)

    def generateMesh(self, psf = None):
        if psf is None :
            psf = self.viewer.layers.selection.active.data
        psf_normalized = (psf - psf.min()) / (psf.max() - psf.min())

        level = Threshold().getInstance("legacy")
        level = level.getThreshold(psf_normalized)
        vertices, faces, _, _ = marching_cubes(psf_normalized,level=level)
        self.viewer.add_surface(
            (vertices, faces),
            name=f"PSF Isosurface (level={level})",
            colormap="viridis",
            opacity=0.7,
        )
        points = self.getContourspoints(psf)
        self.viewer.add_points(
            points,
            name=f"PSF points",
            face_color = "green",
            size=0.5
        )

