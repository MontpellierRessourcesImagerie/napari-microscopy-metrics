import os
import random
import napari
import webbrowser
import numpy as np

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
from microscopy_metrics.scripts.PSFGenerator.PSF import PSFGenerator,PSFWithComaticAberration,PSFWithAstigmatismAberration,PSFWithSphericalAberration

from napari_microscopy_metrics._metrics_widget import Metricstoolpage
from napari_microscopy_metrics._detection_tool_widget import DetectionToolTab
from napari_microscopy_metrics._acquisition_widget import AcquisitionToolPage
from napari_microscopy_metrics._report_widget import ReportToolPage


class Microscopy_Metrics_QWidget(QWidget):
    """A QWidget gathering all the tools for PSF analysis and allowing user to run the whole analysis and generate reports."""

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.DetectionTool = Detection()
        self.MetricTool = Metrics()
        self.FittingTool = Fitting()
        self.reportGenerator = ReportGenerator()

        self.centroidsLayer = None
        self.roisLayer = None
        self.workingLayer = None
        self.outputDir = None
        self.meanSBR = 0
        self.selectedShape = 0
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.tab = QTabWidget()
        self.tab.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.tab.setDocumentMode(True)
        self.acquisitionToolPage = AcquisitionToolPage(self.viewer)
        self.acquisitionToolPage.pixelSizeWidget.signal.scaleUpdate.connect(
            self.updateScaleDetection
        )
        self.acquisitionToolPage.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.tab.addTab(self.acquisitionToolPage, "Acquisition parameters")
        self.detectionToolPage = DetectionToolTab(self.viewer)
        self.detectionToolPage.detectionTool._pixelSize = [
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size Z"),
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size Y"),
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size X"),
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
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size Z"),
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size Y"),
            self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size X"),
        ]
        self.tab.addTab(self.metricsToolPage, "Metrics parameters")

        self.reportToolPage = ReportToolPage(self.viewer)
        self.reportToolPage.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum
        )
        self.tab.addTab(self.reportToolPage, "Report parameters")
        self.runButton = QPushButton("Run analysis")
        self.runButton.setStyleSheet("background-color : green")
        self.runButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.docButton = QPushButton("Documentation")
        self.docButton.setStyleSheet("background-color : blue")
        self.docButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.genButton = QPushButton("Generate random PSF")
        self.genButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(5)
        self.layout().addWidget(self.tab)
        self.layout().addWidget(self.genButton)
        self.layout().addWidget(self.runButton)
        self.layout().addWidget(self.docButton)
        self.runButton.pressed.connect(self.startProcessing)
        self.docButton.pressed.connect(self.openDocumentation)
        self.genButton.pressed.connect(self.generateRandomPSF)
        self.viewer.mouse_double_click_callbacks.append(
            self.onMouseDoubleClick
        )

    def startProcessing(self):
        """Function to start the whole analysis process .
        Raises:
            ValueError: Raised when there is a problem with the selection of the layer to analyze (missing layer, incorrect type, etc.)
        """
        self.workingLayer = self.viewer.layers.selection.active
        self.imageAnalyzer = None
        if self.workingLayer is None or not isinstance(
            self.workingLayer, napari.layers.Image
        ):
            show_error("Please, select a valid layer of type Image")
            return
        self.detectionToolPage.erase_Layers()
        self.runButton.setEnabled(False)
        self.apply_detect_psf()

    def apply_detect_psf(self):
        """Function to update DetectionTool with the image and parameters setup by user in the widget and start a worker for bead detection
        Raises:
            ValueError: Raised when there is a problem with the data of the image selected (missing data, incorrect format, etc.)
        """
        image = self.workingLayer.data
        parametersDetection = (
            self.detectionToolPage.detectionParameters.detectionToolWidget.createDatas()
        )
        parametersDetection.sendDatas(self.DetectionTool)
        self.DetectionTool._image = image
        parametersThreshold = (
            self.detectionToolPage.detectionParameters.widgetThreshold.createDatas()
        )
        parametersThreshold.sendDatas(self.DetectionTool._detectionTool)
        parametersROI = (
            self.detectionToolPage.detectionParameters.widgetRejection.createDatas()
        )
        parametersROI.sendDatas(self.DetectionTool)
        parametersPixelSize = self.acquisitionToolPage.pixelSizeWidget.createDatas()
        parametersPixelSize.sendDatas(self.DetectionTool)
        self.outputDir = os.path.expanduser("~/")
        if (
            self.workingLayer is not None
            and hasattr(self.workingLayer, "source")
            and self.workingLayer.source.path
        ):
            imagePath = self.workingLayer.source.path
            self.outputDir = os.path.dirname(imagePath)
            self.outputDir = os.path.join(
                self.outputDir, f"{self.workingLayer.name}_analysis"
            )
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
            ValueError: Raised when there is a problem with the data of the beads detected (missing data, incorrect format, etc.)
        """
        if (
            self.DetectionTool._imageAnalyzer is None
            or len(self.DetectionTool._imageAnalyzer._beadAnalyzer) == 0
        ):
            raise ValueError("There are no bead detected !")
        else:
            self.imageAnalyzer = self.DetectionTool._imageAnalyzer
            self.imageAnalyzer._path = self.outputDir
        self.displayLayers()
        self.applyPrefittingMetrics()

    def applyPrefittingMetrics(self):
        """Function to update MetricTool with the image and parameters setup by user in the widget and start a worker for prefitting metrics calculation
        Raises:
            ValueError: Raised when there is a problem with the data of the image analyzed (missing data, incorrect format, etc.)
        """
        self.MetricTool._imageAnalyzer = self.imageAnalyzer
        parametersPixelSize = self.acquisitionToolPage.pixelSizeWidget.createDatas()
        parametersPixelSize.sendDatas(self.MetricTool)
        parametersROI = (
            self.detectionToolPage.detectionParameters.widgetRejection.createDatas()
        )
        parametersROI.sendDatas(self.MetricTool)
        parametersMicroscope = (
            self.acquisitionToolPage.microscopeWidget.createDatas()
        )
        parametersMicroscope.sendDatas(self.MetricTool)
        worker = create_worker(
            self.MetricTool.runPrefittingMetrics,
            _progress={"desc": "Metrics calculation..."},
        )
        worker.finished.connect(self.prefittingFinished)
        worker.errored.connect(self.onReportFinished)
        worker.start()

    def prefittingFinished(self):
        """Function to update result collection after prefitting metrics calculation and start fitting process"""
        self.metricsToolPage.printResults(self.imageAnalyzer._meanSBR)
        self.meanSBR = self.imageAnalyzer._meanSBR
        for bead in self.imageAnalyzer._beadAnalyzer:
            if bead._rejected == False and bead._roi is not None:
                bead._metricTool.meshBuilder.saveMesh(os.path.join(self.getActivePath(bead._id), f"bead_{bead._id}_mesh.obj"))
        self.generateMesh()
        self.applyFitting()

    def applyFitting(self):
        """Function to update FittingTool with the image and parameters setup by user in the widget and start a worker for fitting process
        Raises:
            ValueError: Raised when there is a problem with the data of the image analyzed (missing data, incorrect format, etc.)
        """
        self.FittingTool._imageAnalyzer = self.imageAnalyzer
        self.FittingTool.outputDir = self.outputDir

        parametersFitting = (
            self.metricsToolPage.widgetFittingChoice.createDatas()
        )
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
            ValueError: Raised when there is a problem with the data of the beads analyzed or the fitting results (missing data, incorrect format, etc.)
        """
        if (
            self.imageAnalyzer._beadAnalyzer is None
            or len(self.imageAnalyzer._beadAnalyzer) == 0
        ):
            raise ValueError("There are no bead analyzed !")
        for bead in self.imageAnalyzer._beadAnalyzer:
            if bead._rejected == False and bead._roi is not None:
                FWHM = bead._fitTool.fwhms
                bead._metricTool.lateralAsymmetryRatio(FWHM)
                bead._metricTool.sphericity()
                bead._metricTool.comaticity()
                bead._metricTool.sphericalAberration()
                bead._metricTool.astigmatism(bead._fitTool.getMu(), bead._fitTool.getSigma())
                bead._fitTool.computeContrast()
                bead._metricTool.ellipsRatio()
                bead._metricTool.skeletonizePath()
        self.generatePaths()
        self.generateCentroidsPath()
        self.imageAnalyzer._meanComaticity = np.mean([bead._metricTool._comaticity for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
        self.imageAnalyzer._meanSphericalAberration = np.mean([bead._metricTool._sphericalAberration for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
        self.imageAnalyzer._meanAstigmatism = np.mean([bead._metricTool._astigmatism for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
        self.imageAnalyzer._meanContrast = np.mean([bead._fitTool.contrast for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
        self.imageAnalyzer._meanEllipsRatio = np.mean([bead._metricTool._ellipsRatio for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
        self.imageAnalyzer._meanOrientation = np.mean([bead._metricTool._orientation for bead in self.imageAnalyzer._beadAnalyzer if bead._rejected == False])
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
        """Function to generate a PDF report with all the results of the analysis using ReportGenerator"""
        listReports = self.reportToolPage.getListReports()
        for report in listReports:
            yield {"desc": f"Generating {report}..."}
            PDFGenerator = ReportGenerator().getInstance(report)
            PDFGenerator._inputDir = self.outputDir
            PDFGenerator._imageAnalyzer = self.imageAnalyzer
            PDFGenerator._detectionDatas = (
                self.detectionToolPage.detectionParameters.detectionToolWidget.createDatas().toDict()
            )
            PDFGenerator._thresholdDatas = (
                self.detectionToolPage.detectionParameters.widgetThreshold.createDatas().toDict()
            )
            PDFGenerator._roiDatas = (
                self.detectionToolPage.detectionParameters.widgetRejection.createDatas().toDict()
            )
            PDFGenerator._fittingDatas = (
                self.metricsToolPage.widgetFittingChoice.createDatas().toDict()
            )
            PDFGenerator._microscopeDatas = (
                self.acquisitionToolPage.microscopeWidget.createDatas().toDict()
            )
            PDFGenerator.generateReport(self.outputDir)

    def onReportFinished(self):
        """Function to update plugin interface after report generation and open the HTML report in a web browser"""
        show_info(
            "Report generation finished! You can find the report in the same folder as your image with the name <image_name>_analysis_result.pdf"
        )
        self.runButton.setEnabled(True)

    def openBrowser(self):
        """Function to open the HTML report corresponding to the bead selected by user in napari viewer in a web browser"""
        activePath = self.getActivePath(index=self.selectedShape)
        activePath = os.path.join(activePath, "report.html")
        webbrowser.open(activePath)

    def openDocumentation(self):
        """Function to open the documentation webPage in a web browser"""
        documentationPath = "https://montpellierressourcesimagerie.github.io/napari-microscopy-metrics/index.html"
        webbrowser.open(documentationPath)

    def onMouseDoubleClick(self, layer, event):
        """Function to open the HTML report corresponding to the bead selected by user in napari viewer when user double click on a ROI shape in napari viewer
        Args:
            layer (napari.layers.Layer): The layer on which the double click event happened
            event (napari.utils.events.Event): The double click event
        """
        clickPos = self.viewer.cursor.position / self.workingLayer.scale

        if self.roisLayer is None:
            return
        beads = self.imageAnalyzer._beadAnalyzer
        for bead in beads:
            if bead._rejected == False and bead._roi is not None:
                shape = bead._roi
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
                    self.selectedShape = bead._id
                    self.openBrowser()
                    event.handled = True
                    return

    def getActivePath(self, index):
        """Function to get the path of the folder corresponding to the bead selected by user in napari viewer
        Args:
            index (int): The index of the bead selected corresponding to the index of the ROI shape in napari viewer
        Returns:
            str: The path of the folder corresponding to the bead selected by user in napari viewer
        """
        activePath = os.path.join(self.outputDir, f"bead_{index}")
        if not os.path.exists(activePath):
            os.makedirs(activePath)
        return activePath

    def displayLayers(self):
        """Function to display the layers corresponding to the beads detected and the ROIs extracted in napari viewer after detection and update the scale of all layers according to the pixel size setup by user in acquisitionToolPage"""
        if len(self.imageAnalyzer._beadAnalyzer) > 0:
            beads = [
                bead
                for bead in self.imageAnalyzer._beadAnalyzer
                if not bead._rejected
            ]
            if self.centroidsLayer is None:
                self.centroidsLayer = self.viewer.add_points(
                    [
                        bead._centroid
                        for bead in self.imageAnalyzer._beadAnalyzer
                        if not bead._rejected
                    ],
                    name="PSF detected",
                    face_color="red",
                    opacity=0.5,
                    size=2,
                )
            else:
                self.centroidsLayer.data = [
                    bead._centroid
                    for bead in self.imageAnalyzer._beadAnalyzer
                    if not bead._rejected
                ]
            self.detectionToolPage.resultsLabel.setText(
                f"Here are the results of the detection:\n- {len(self.imageAnalyzer._beadAnalyzer)} bead(s) detected\n- {len([bead for bead in self.imageAnalyzer._beadAnalyzer if not bead._rejected])} ROI(s) extracted"
            )
        else:
            show_warning("No PSF found or incorrect format.")
        if len(beads) > 0:
            features = {"label": [f"bead_{bead._id}" for bead in beads]}
            text = {
                "string": "{label}",
                "anchor": "upper_left",
                "translation": [5, -5, 5],
                "size": 8,
                "color": "green",
            }
            if self.roisLayer is None:
                self.roisLayer = self.viewer.add_shapes(
                    [bead._roi for bead in beads],
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
                    [bead._roi for bead in beads],
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
        """A method to update the scale of the detection and metrics tools when user update pixel size in acquisitionToolPage.
        Args:
            scale (list): List of 3 values corresponding to pixel size in Z, Y and X of the image.
        """
        self.detectionToolPage.detectionTool._pixelSize = scale
        self.metricsToolPage.spacing = scale

    def generateRandomPSF(self):
        """Function to generate a random PSF and display it in the napari viewer"""
        size = 100
        dxy = self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size X")
        dz = self.acquisitionToolPage.pixelSizeWidget.options.value("Pixel size Z")
        ni0 = self.acquisitionToolPage.microscopeWidget.options.value("Refraction index")
        wvl = self.acquisitionToolPage.microscopeWidget.options.value("Emission wavelength") / 1000
        NA = self.acquisitionToolPage.microscopeWidget.options.value("Numerical aperture")
        aberrationType = random.choice([None,"comatic","astigmatism","spherical"])
        if aberrationType == "comatic":
            psf = PSFWithComaticAberration(size, dxy, dz, ni0, ni0, wvl, NA).psf
        elif aberrationType == "astigmatism":
            psf = PSFWithAstigmatismAberration(size, dxy, dz, ni0, ni0, wvl, NA).psf
        elif aberrationType == "spherical":
            psf = PSFWithSphericalAberration(size, dxy, dz, ni0, wvl, NA).psf
        else:
            psf = PSFGenerator(size, dxy, dz, ni0, ni0, wvl, NA).psf
        psf = psf.reshape((size, size, size))
        if aberrationType == None : 
            aberrationType = "no"
        self.viewer.add_image(psf, name=f"PSF with {aberrationType} aberration")

    def generateMesh(self):
        """Function to generate a 3D mesh corresponding to the contours of the PSF and display it in the napari viewer

        Args:
            psf (np.ndarray, optional): The PSF for which to generate a mesh. Defaults to None.
        """
        all_vertices = []
        all_faces = []
        all_values = []
        vertex_offset = 0
        for bead in self.imageAnalyzer._beadAnalyzer:
            if bead._rejected == False and bead._roi is not None:
                vertices = np.array(bead._metricTool.meshBuilder._vertices) 
                faces = np.array(bead._metricTool.meshBuilder._faces)
                vertices[:, 1] += bead._roi[0][1]
                vertices[:, 2] += bead._roi[0][2]
                offset_faces = faces + vertex_offset
                all_vertices.append(vertices)
                all_faces.append(offset_faces)
                for i in range(len(vertices)):
                    all_values.append(bead._metricTool.meshBuilder._curvature[i])
                vertex_offset += len(vertices)
        
        if all_vertices:
            vertices = np.concatenate(all_vertices, axis=0)
            faces = np.concatenate(all_faces, axis=0)
            values = np.array(all_values)
            maxVal = 5.0
            c_min, cmax = -maxVal, maxVal
            self.viewer.add_surface(
                (vertices, faces, values),
                name=f"PSF_Isosurfaces.obj",
                colormap="coolwarm",
                opacity=0.7,
                contrast_limits=(c_min, cmax),
            )
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixelSize
        self.viewer.reset_view()

    def generatePaths(self):
        """Function to generate the paths of the folders corresponding to each bead analyzed and create these folders if they don't exist yet"""
        import pandas as pd
        all_paths = []
        all_tables = []
        for bead in self.imageAnalyzer._beadAnalyzer:
            if bead._rejected == False and bead._roi is not None:
                skeleton = bead._metricTool._pathSkeleton
                if skeleton is not None and not skeleton.n_paths == 0:
                    offset = np.array([0.0, bead._roi[0][1], bead._roi[0][2]])
                    shifted_paths = [skeleton.path_coordinates(i) + offset for i in range(skeleton.n_paths)]
                    all_paths.extend(shifted_paths)
                    paths_table = bead._metricTool._summary
                    paths_table['path_id'] = np.arange(skeleton.n_paths)
                    paths_table['random_path_id'] = np.random.default_rng().permutation(skeleton.n_paths)
                    all_tables.append(paths_table)
        if not all_paths:
            return
        combinedTables = pd.concat(all_tables, ignore_index=True)
        self.viewer.add_shapes(
            all_paths,
            shape_type="path",
            properties = combinedTables,
            edge_color='random_path_id',
            edge_colormap='tab10',
            name="PSF skeleton paths",
        )
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixelSize
        self.viewer.reset_view()

    def generateCentroidsPath(self):
        """Function to generate the path of the folder corresponding to the centroids of the beads analyzed and create this folder if it doesn't exist yet"""
        centroids = []
        for bead in self.imageAnalyzer._beadAnalyzer:
            if bead._rejected == False and bead._roi is not None:
                beadPath = []
                for z,centroid in enumerate(bead._metricTool._centroids):
                    beadPath.append([centroid[0], bead._roi[0][1] + centroid[1], bead._roi[0][2] + centroid[2]])
                if beadPath:
                    centroids.append(np.array(beadPath))
        if not centroids:
            return
        self.viewer.add_shapes(
            centroids,
            shape_type="path",
            edge_color='red',
            name="Centroids paths",
        )
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixelSize
        self.viewer.reset_view()
                
