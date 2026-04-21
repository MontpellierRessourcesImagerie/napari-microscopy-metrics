import napari
from pathlib import Path

from qtpy.QtGui import QIcon
from napari.settings import get_settings
from napari.qt.threading import create_worker
from qtpy.QtCore import QSize
from napari.utils.notifications import show_warning
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QGroupBox,
)

from microscopy_metrics.detection import Detection

from napari_microscopy_metrics.widgets.DetectionToolWidget import (
    DetectionToolWidget,
)
from napari_microscopy_metrics.widgets.ThresholdWidget import ThresholdWidget
from napari_microscopy_metrics.widgets.ROIWidget import RoiWidget


class DetectionParametersWidget(QWidget):
    """A napari widget form for PSF detection parameters.
    It contains a DetectionToolWidget for setting detection parameters, a ThresholdWidget for setting threshold parameters and a RoiWidget for setting region of interest parameters.
    It is used in DetectionToolTab widget to create a parameters window and send parameters to the detection tool when applying detection.
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.detectionGroup = QGroupBox("Detection parameters")
        self.groupLayout = QVBoxLayout()
        self.detectionGroup.setLayout(self.groupLayout)

        self.detectionToolLayout = QVBoxLayout()
        self.detectionToolWidget = DetectionToolWidget(self.viewer)
        self.detectionToolLayout.addWidget(self.detectionToolWidget)
        self.groupLayout.addLayout(self.detectionToolLayout)

        self.layer = None
        self.oldContrastLimits = None

        self.thresholdGroup = QGroupBox("Threshold parameters")
        self.groupThresholdLayout = QVBoxLayout()
        self.thresholdGroup.setLayout(self.groupThresholdLayout)
        self.thresholdToolLayout = QVBoxLayout()
        self.widgetThreshold = ThresholdWidget(self.viewer)
        self.thresholdToolLayout.addWidget(self.widgetThreshold)
        self.groupThresholdLayout.addLayout(self.thresholdToolLayout)

        self.ROIGroup = QGroupBox("ROI parameters")
        self.groupROILayout = QVBoxLayout()
        self.ROIGroup.setLayout(self.groupROILayout)
        self.ROIToolLayout = QVBoxLayout()
        self.widgetRejection = RoiWidget(self.viewer)
        self.ROIToolLayout.addWidget(self.widgetRejection)
        self.groupROILayout.addLayout(self.ROIToolLayout)

        layout.addWidget(self.detectionGroup)
        layout.addWidget(self.thresholdGroup)
        layout.addWidget(self.ROIGroup)
        self.setLayout(layout)


class DetectionToolTab(QWidget):
    """A napari widget form for PSF detection.
    It contains a button to open the parameters window and a button to apply detection with current parameters
    It also manage the display of detection results with new layers in napari viewer.
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.countWindows = 0
        self.detectionTool = Detection()
        self.detectionParameters = DetectionParametersWidget(self.viewer)

        self.detectedBeadsLayer = None
        self.ROILayer = None

        self.parametersButton = QPushButton()
        self.parametersButton.clicked.connect(self.openParametersWindow)
        iconPath = self.getLogoPath(get_settings().appearance.theme)
        self.parametersButton.setIcon(QIcon(str(iconPath)))
        self.parametersButton.setIconSize(QSize(35, 35))
        self.parametersButton.setFixedSize(35, 35)
        self.parametersButton.setToolTip("Open detection configurator")

        self.detectionButton = QPushButton("Visualize beads detection")
        self.detectionButton.setToolTip(
            "Get a preview of detection with current parameters"
        )
        self.detectionButton.clicked.connect(self.apply)

        self.resultsLabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.parametersButton)
        layout.addWidget(self.detectionButton)
        layout.addWidget(self.resultsLabel)
        layout.addStretch()
        self.setLayout(layout)

        self.viewer.layers.events.removed.connect(self.onLayerRemoved)

    def onLayerRemoved(self, event):
        """Manage the suppression of ROI and _centroids layers

        Args:
            event (QEvent): Informations about the triggering event
        """
        if (
            hasattr(self, "detectedBeadsLayer")
            and self.detectedBeadsLayer == event.value
        ):
            self.detectedBeadsLayer = None
        if hasattr(self, "ROILayer") and self.ROILayer == event.value:
            self.ROILayer = None

    def openParametersWindow(self):
        """A method to create parameters window and limit the maximum window number to one."""
        if self.countWindows == 0:
            self.parametersWindow = QDialog(self)
            self.parametersWindow.setWindowTitle("Detection parameters")
            self.parametersWindow.setModal(False)
            self.parametersWindow.finished.connect(
                self.onParametersWindowClosed
            )
            parametersLayout = QVBoxLayout()
            parametersLayout.addWidget(self.detectionParameters)
            self.parametersWindow.setLayout(parametersLayout)
            self.parametersWindow.show()
            self.countWindows += 1

    def onParametersWindowClosed(self, result):
        """Called when parameters window is closed to unlock the possibility to open another one and remove threshold preview.

        Args:
            result : Parameter sent by the window when closed
        """
        self.countWindows -= 1
        if self.detectionParameters.widgetThreshold.layer is not None:
            self.detectionParameters.widgetThreshold.layer.contrast_limits = (
                self.detectionParameters.widgetThreshold.oldContrastLimits
            )
            self.detectionParameters.widgetThreshold.layer.colormap = "gray"
            self.detectionParameters.widgetThreshold.layer.blending = (
                "additive"
            )

    def erase_Layers(self):
        """A method to delete all layers created by this widget"""
        if self.ROILayer:
            self.viewer.layers.remove(self.ROILayer)
        if self.detectedBeadsLayer:
            self.viewer.layers.remove(self.detectedBeadsLayer)

    def getLogoPath(self, theme):
        """A method to automatically return the logo corresponding to the application theme.

        Args:
            theme (napari.theme): The actual theme of the napari application.

        Returns:
            Path: path to the logo corresponding to the theme.
        """
        logoDirectory = Path(__file__).parent / "res" / "drawable"
        if theme == "dark":
            return logoDirectory / "logo_dark.png"
        else:
            return logoDirectory / "logo_light.png"

    def apply(self):
        """Called when validating to launch beads detection and extraction with current parameters. It is not an analysis, only a detection preview."""
        self.detectionTool.image = self.viewer.layers.selection.active.data
        parametersDetection = (
            self.detectionParameters.detectionToolWidget.createDatas()
        )
        parametersDetection.sendDatas(self.detectionTool)
        parametersThreshold = (
            self.detectionParameters.widgetThreshold.createDatas()
        )
        parametersThreshold.sendDatas(self.detectionTool._detectionTool)
        parametersROI = self.detectionParameters.widgetRejection.createDatas()
        parametersROI.sendDatas(self.detectionTool)
        kwargs = {"cropPsf": False}
        worker = create_worker(
            self.detectionTool.run,
            **kwargs,
            _progress={"desc": "Detecting beads..."},
        )
        worker.finished.connect(self.displayResult)
        worker.errored.connect(lambda: self.detectionButton.setEnabled(True))
        self.detectionButton.setEnabled(False)
        worker.start()

    def displayResult(self):
        """A method to display detected centroids and region of interest with new layers."""
        workingLayer = self.viewer.layers.selection.active
        if len(self.detectionTool._imageAnalyze._beadAnalyze) > 0:
            if self.ROILayer is None:
                self.ROILayer = self.viewer.add_shapes(
                    [
                        bead._roi
                        for bead in self.detectionTool._imageAnalyze._beadAnalyze
                        if not bead._rejected
                    ],
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            else:
                self.viewer.layers.remove(self.ROILayer)
                self.ROILayer = self.viewer.add_shapes(
                    [
                        bead._roi
                        for bead in self.detectionTool._imageAnalyze._beadAnalyze
                        if not bead._rejected
                    ],
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            if self.detectedBeadsLayer is None:
                self.detectedBeadsLayer = self.viewer.add_points(
                    [
                        bead._centroid
                        for bead in self.detectionTool._imageAnalyze._beadAnalyze
                        if not bead._rejected
                    ],
                    name="PSF detected",
                    face_color="red",
                    opacity=0.5,
                    size=2,
                )
            else:
                self.detectedBeadsLayer.data = [
                    bead._centroid
                    for bead in self.detectionTool._imageAnalyze._beadAnalyze
                    if not bead._rejected
                ]
            self.resultsLabel.setText(
                f"Here are the results of the detection:\n- {len(self.detectionTool._imageAnalyze._beadAnalyze)} bead(s) detected\n- {len([bead for bead in self.detectionTool._imageAnalyze._beadAnalyze if not bead._rejected])} ROI(s) extracted"
            )
        else:
            show_warning("No PSF found or incorrect format.")
        self.detectionButton.setEnabled(True)
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.detectionTool._pixelSize
        self.viewer.layers.selection.active = workingLayer
        self.viewer.reset_view()
