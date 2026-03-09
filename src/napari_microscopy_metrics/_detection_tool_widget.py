"""
This module contains a napari widgets for PSF detection
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
from microscopy_metrics.detection import *
from microscopy_metrics.metrics import *
from microscopy_metrics.detection_tool import Peak_Local_Max_Detector
import napari
from napari.settings import get_settings
from napari.utils.notifications import *
from .json_utils import *
from autooptions import *
from napari.qt.threading import create_worker
from scipy import ndimage as ndi


class ParamsSignal(QObject):
    """Class for the declaration of update parameters signal"""

    params_updated = Signal(dict)


class DetectionToolWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.options_sliders = self.getSliders()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        self.widget = OptionsWidget(self.viewer,self.options)
        self.tool_choice_widget = self.widget.mainLayout.itemAt(0).itemAt(1).widget()
        self.tool_choice_widget.currentTextChanged.connect(self._selected_action)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)

        self.params_stack = QStackedWidget()

        self.peak_method_widget = QWidget()
        self.peak_method_layout = QVBoxLayout()
        self.peak_method_layout.setContentsMargins(0, 0, 0, 0)
        self.peak_method_layout.setSpacing(2)
        self.min_distance_detection = QSlider(Qt.Horizontal)
        self.min_distance_detection.setRange(0, 20)
        self.min_distance_detection.setValue(self.options_sliders.value("Min dist"))
        self.min_distance_detection.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.min_distance_label = QLabel("Minimal distance: " + str(self.min_distance_detection.value()))
        self.min_distance_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.peak_method_layout.addWidget(self.min_distance_label)
        self.peak_method_layout.addWidget(self.min_distance_detection)
        self.peak_method_widget.setLayout(self.peak_method_layout)

        self.blob_method_widget = QWidget()
        self.blob_method_layout = QVBoxLayout()
        self.blob_sigma_slider = QSlider(Qt.Horizontal)
        self.blob_sigma_slider.setRange(1, 10)
        self.blob_sigma_slider.setValue(self.options_sliders.value("Sigma"))
        self.blob_sigma_label = QLabel("Sigma: " + str(self.blob_sigma_slider.value()))
        self.blob_method_layout.addWidget(self.blob_sigma_label)
        self.blob_method_layout.addWidget(self.blob_sigma_slider)
        self.blob_method_widget.setLayout(self.blob_method_layout)

        self.centroid_method_widget = QWidget()
        self.centroid_method_layout = QVBoxLayout()
        self.centroid_method_widget.setLayout(self.centroid_method_layout)

        self.params_stack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.params_stack.addWidget(self.peak_method_widget)
        self.params_stack.addWidget(self.blob_method_widget)
        self.params_stack.addWidget(self.centroid_method_widget)

        self.widget.mainLayout.addWidget(self.params_stack)
        self.widget.addApplyButton(self.apply)
        self.setLayout(layout)
        self._selected_action(self.tool_choice_widget.currentText())
        self.min_distance_detection.valueChanged.connect(self._update_min_distance)
        self.blob_sigma_slider.valueChanged.connect(self._update_sigma)

    @classmethod
    def getOptions(cls):
        options = Options("Detection Parameters","Set parameters for detection tool")
        options.addChoice(name="Detection tool",value="Centroids",choices=[x for x in Detection_Tool._detection_classes])
        options.load()
        return options

    def getSliders(self):
        options_sliders = Options("Sliders value","Store value of sliders")
        options_sliders.addInt(name="Min dist",value=1)
        options_sliders.addInt(name="Sigma",value=3)
        options_sliders.load()
        return options_sliders

    def _selected_action(self, value):
        """Update the display for selected tool and assign the value in params"""
        index = self.tool_choice_widget.currentIndex()
        if index >= 2:
            index = index - 1
        self.params_stack.setCurrentIndex(index)

    def apply(self):
        self.options_sliders.save()

    def _update_min_distance(self, value):
        """Update the label for minimal distance and assign the value in params"""
        self.min_distance_label.setText("Minimal distance: " + str(value))
        self.options_sliders.items["Min dist"]["value"] = value

    def _update_sigma(self, value):
        """Update the label for sigma and assign the value in params"""
        self.blob_sigma_label.setText("Sigma: " + str(value))
        self.options_sliders.items["Sigma"]["value"] = value


class ThresholdWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.options_sliders = self.getSliders()
        self.widget = None
        self.createLayout()
        self.layer = None
        self.old_contrast_limits = []

    def createLayout(self):
        self.widget = OptionsWidget(self.viewer,self.options)
        self.tool_choice_widget = self.widget.mainLayout.itemAt(0).itemAt(1).widget()
        self.tool_choice_widget.currentTextChanged.connect(self._selected_action)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)

        self.params_stack = QStackedWidget()

        self.threshold_rel_widget = QWidget()
        self.threshold_rel_layout = QVBoxLayout()
        self.threshold_rel_layout.setContentsMargins(0, 0, 0, 0)
        self.threshold_rel_layout.setSpacing(2)
        self.threshold_rel = QSlider(Qt.Horizontal)
        self.threshold_rel.setRange(0, 100)
        self.threshold_rel.setValue(self.options_sliders.value("threshold"))
        self.threshold_rel_label = QLabel(
            "Relative threshold: " + str(self.threshold_rel.value() / 100)
        )
        self.threshold_rel_layout.addWidget(self.threshold_rel_label)
        self.threshold_rel_layout.addWidget(self.threshold_rel)
        self.threshold_rel_widget.setLayout(self.threshold_rel_layout)
        self.empty_widget = QWidget()
        self.empty_layout = QVBoxLayout()
        self.empty_widget.setLayout(self.empty_layout)
        self.params_stack.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.params_stack.addWidget(self.threshold_rel_widget)
        self.params_stack.addWidget(self.empty_widget)
        self.widget.mainLayout.addWidget(self.params_stack)
        self.widget.addApplyButton(self.apply)
        self.setLayout(layout)
        self._selected_action(self.tool_choice_widget.currentText())
        self.threshold_rel.valueChanged.connect(self._update_threshold)

    @classmethod
    def getOptions(cls):
        options = Options("Threshold parameters","Set parameters for threshold")
        options.addChoice(name="Threshold",value="otsu",choices=[x for x in Threshold._threshold_classes])
        options.load()
        return options

    def getSliders(self):
        options_sliders = Options("Sliders value","Store value of sliders")
        options_sliders.addInt(name="threshold",value=50)
        options_sliders.load()
        return options_sliders

    def _selected_action(self, value):
        """Update the display for selected tool and assign the value in params"""
        if value == "manual":
            self.params_stack.setCurrentIndex(0)
        else :
            self.params_stack.setCurrentIndex(1)

    def apply(self):
        self.options_sliders.save()
        if self.tool_choice_widget.currentText() != "manual":
            self.display_threshold(self.tool_choice_widget.currentText())

    def _update_threshold(self, value):
        """Update the label for relative threshold and assign the value in params"""
        self.threshold_rel_label.setText(
            "Relative threshold: " + str(value / 100)
        )
        self.options_sliders.items["threshold"]["value"] = value
        self.display_threshold("manual",value=value/100)

    def display_threshold(self,threshold_str,value=0.5):
        if isinstance(self.viewer.layers.selection.active, napari.layers.Image):
            if self.layer != self.viewer.layers.selection.active and self.layer is not None:
                self.layer.contrast_limits = self.old_contrast_limits
                self.layer.colormap = "gray"
                self.layer.blending = "additive"
                self.layer = None
            if self.layer is None or self.old_contrast_limits is None:
                self.layer = self.viewer.layers.selection.active
                self.old_contrast_limits = self.layer.contrast_limits

            threshold = Threshold.get_instance(threshold_str)
            if threshold_str == "manual":
                threshold.rel_threshold = value
            value_threshold = threshold.get_threshold(self.layer.data)
            self.layer.contrast_limits = [max(min(value_threshold + np.min(self.layer.data),self.old_contrast_limits[1]-1),self.old_contrast_limits[0]),self.old_contrast_limits[1]]
            self.layer.colormap = 'HiLo'
            self.layer.blending = "additive"

class RoiWidget(QWidget):
    def __init__(self,viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.options = self.getOptions()
        self.options_sliders = self.getSliders()
        self.widget = None
        self.createLayout()

    def createLayout(self):
        self.widget = OptionsWidget(self.viewer,self.options)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.crop_factor = QSlider(Qt.Horizontal)
        self.crop_factor.setRange(1, 10)
        self.crop_factor.setValue(self.options_sliders.value("crop factor"))
        self.crop_factor_label = QLabel("Crop factor: " + str(self.crop_factor.value()))
        self.widget.mainLayout.addWidget(self.crop_factor_label)
        self.widget.mainLayout.addWidget(self.crop_factor)
        self.widget.addApplyButton(self.apply)
        self.setLayout(layout)
        self.crop_factor.valueChanged.connect(self._update_crop_factor)

    @classmethod
    def getOptions(cls):
        options = Options("Extraction parameters","Set parameters for extraction")
        options.addFloat(name="Theoretical bead size (µm)",value=0.6)
        options.addFloat(name="Z axis rejection margin (µm)",value=0.5)
        options.addFloat(name="Inner annulus distance to bead (µm)",value=1.0)
        options.addFloat(name="Annulus thickness (µm)",value=2.0)
        options.load()
        return options

    def getSliders(self):
        options_sliders = Options("Crop factor value","Store value of crop factor")
        options_sliders.addInt(name="crop factor",value=5)
        options_sliders.load()
        return options_sliders


    def apply(self):
        self.options_sliders.save()

    def _update_crop_factor(self, value):
        """Updates the label for crop factor and assign the value in params"""
        self.crop_factor_label.setText("Crop factor: " + str(value))
        self.options_sliders.items["crop factor"]["value"] = value



class Detection_Parameters_Widget(QWidget):
    """Widget for processing PSF detection and extraction

    Parameters
    ----------
    viewer : napari.viewer.Viewer
        The napari viewer were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.signal = ParamsSignal()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.detection_group = QGroupBox("Detection parameters")
        self.group_layout = QVBoxLayout()
        self.detection_group.setLayout(self.group_layout)

        self.detection_tool_layout = QVBoxLayout()
        self.detection_tool_widget = DetectionToolWidget(self.viewer)
        self.detection_tool_layout.addWidget(self.detection_tool_widget)
        self.group_layout.addLayout(self.detection_tool_layout)

        self.layer = None
        self.old_contrast_limits = None

        self.threshold_group = QGroupBox("Threshold parameters")
        self.group_threshold_layout = QVBoxLayout()
        self.threshold_group.setLayout(self.group_threshold_layout)
        self.threshold_tool_layout = QVBoxLayout()
        self.widget_threshold = ThresholdWidget(self.viewer)
        self.threshold_tool_layout.addWidget(self.widget_threshold)
        self.group_threshold_layout.addLayout(self.threshold_tool_layout)

        self.ROI_group = QGroupBox("ROI parameters")
        self.group_ROI_layout = QVBoxLayout()
        self.ROI_group.setLayout(self.group_ROI_layout)
        self.ROI_tool_layout = QVBoxLayout()
        self.widget_rejection = RoiWidget(self.viewer)
        self.ROI_tool_layout.addWidget(self.widget_rejection)
        self.group_ROI_layout.addLayout(self.ROI_tool_layout)

        layout.addWidget(self.detection_group)
        layout.addWidget(self.threshold_group)
        layout.addWidget(self.ROI_group)
        self.setLayout(layout)


class Detection_Tool_Tab(QWidget):
    """The main widget of the detection tool

    Parameter
    ---------
    viewer : napari.viewer.Viewer
        The environment were the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.count_windows = 0
        self.DetectionTool = Detection()
        self.DetectionParameters = Detection_Parameters_Widget(self.viewer)

        self.filtered_layer = None
        self.filter_layer = None

        self.parameters_btn = QPushButton()
        self.parameters_btn.clicked.connect(self._open_parameters_window)
        icon_path = self.get_logo_path(get_settings().appearance.theme)
        self.parameters_btn.setIcon(QIcon(str(icon_path)))
        self.parameters_btn.setIconSize(QSize(35, 35))
        self.parameters_btn.setFixedSize(35, 35)

        self.detection_btn = QPushButton("Visualize beads detection")
        self.detection_btn.clicked.connect(self.apply)

        self.results_label = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.addWidget(self.parameters_btn)
        layout.addWidget(self.detection_btn)
        layout.addWidget(self.results_label)
        layout.addStretch()
        self.setLayout(layout)

        self.viewer.layers.events.removed.connect(self._on_layer_removed)

    def _on_layer_removed(self, event):
        """Manage the suppression of ROI and centroids layers"""
        if (
            hasattr(self, "filtered_layer")
            and self.filtered_layer == event.value
        ):
            self.filtered_layer = None
        if hasattr(self, "filter_layer") and self.filter_layer == event.value:
            self.filter_layer = None

    def _open_parameters_window(self):
        """Open the parameters window"""
        if self.count_windows == 0:
            self.parameters_window = QDialog(self)
            self.parameters_window.setWindowTitle("Detection parameters")
            self.parameters_window.setModal(False)
            self.parameters_window.finished.connect(
                self._on_parameters_window_closed
            )
            parameters_layout = QVBoxLayout()
            parameters_layout.addWidget(self.DetectionParameters)
            self.parameters_window.setLayout(parameters_layout)
            self.parameters_window.show()
            self.count_windows += 1

    def _on_parameters_window_closed(self, result):
        """Catch the close event of the window and update the counter"""
        self.count_windows -= 1
        if self.DetectionParameters.widget_threshold.layer is not None : 
            self.DetectionParameters.widget_threshold.layer.contrast_limits = self.DetectionParameters.widget_threshold.old_contrast_limits
            self.DetectionParameters.widget_threshold.layer.colormap = "gray"
            self.DetectionParameters.widget_threshold.layer.blending = "additive"

    def erase_Layers(self):
        """Delete all layers made by this wiget"""
        if self.filter_layer:
            self.viewer.layers.remove(self.filter_layer)
        if self.filtered_layer:
            self.viewer.layers.remove(self.filtered_layer)

    def get_logo_path(self, theme):
        logo_dir = Path(__file__).parent / "res" / "drawable"
        if theme == "dark":
            return logo_dir / "logo_dark.png"
        else:
            return logo_dir / "logo_light.png"

    def on_theme_change(self):
        icon_path = self.get_logo_path(get_settings().appearance.theme)
        self.parameters_btn.setIcon(QIcon(str(icon_path)))
        self.parameters_btn.setIconSize(QSize(35, 35))
        self.parameters_btn.setFixedSize(35, 35)

    def apply(self):
        self.DetectionTool.image = self.viewer.layers.selection.active.data
        self.DetectionTool._detection_tool = Detection_Tool.get_instance(self.DetectionParameters.detection_tool_widget.options.value("Detection tool"))
        self.DetectionTool._detection_tool._threshold_tool = Threshold.get_instance(self.DetectionParameters.widget_threshold.options.value("Threshold"))
        if self.DetectionParameters.widget_threshold.options.value("Threshold") == "manual":
            self.DetectionTool._detection_tool._threshold_tool.rel_threshold = self.DetectionParameters.widget_threshold.options_sliders.value("threshold")/100
        self.DetectionTool._detection_tool._image = self.viewer.layers.selection.active.data
        self.DetectionTool._detection_tool.sigma = self.DetectionParameters.detection_tool_widget.options_sliders.value("Sigma")
        if isinstance(self.DetectionTool._detection_tool,Peak_Local_Max_Detector):
            self.DetectionTool._detection_tool.min_distance = self.DetectionParameters.detection_tool_widget.options_sliders.value("Min dist")
        self.DetectionTool.crop_factor = self.DetectionParameters.widget_rejection.options_sliders.value("crop factor")
        self.DetectionTool.bead_size = self.DetectionParameters.widget_rejection.options.value("Theoretical bead size (µm)")
        self.DetectionTool.rejection_distance = self.DetectionParameters.widget_rejection.options.value("Z axis rejection margin (µm)")
        kwargs = {"crop_psf": False}
        worker = create_worker(
            self.DetectionTool.run,
            **kwargs,
            _progress={"desc": "Detecting beads..."},
        )
        worker.finished.connect(self.display_Result)
        worker.errored.connect(lambda _: self.detection_btn.setEnabled(True))
        self.detection_btn.setEnabled(False)
        worker.start()

    def display_Result(self):
        working_layer = self.viewer.layers.selection.active
        if (
            isinstance(self.DetectionTool.centroids, np.ndarray)
            and self.DetectionTool.centroids.size > 0
        ):
            if self.filter_layer is None:
                self.filter_layer = self.viewer.add_shapes(
                    self.DetectionTool.rois_extracted,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            else:
                self.viewer.layers.remove(self.filter_layer)
                self.filter_layer = self.viewer.add_shapes(
                    self.DetectionTool.rois_extracted,
                    shape_type="rectangle",
                    name="ROI",
                    edge_color="blue",
                    face_color="transparent",
                )
            if self.filtered_layer is None:
                self.filtered_layer = self.viewer.add_points(
                    self.DetectionTool.centroids,
                    name="PSF detected",
                    face_color="red",
                    opacity=0.5,
                    size=2,
                )
            else:
                self.filtered_layer.data = self.DetectionTool.centroids
            self.results_label.setText(
                f"Here are the results of the detection:\n- {len(self.DetectionTool.centroids)} bead(s) detected\n- {len(self.DetectionTool.rois_extracted)} ROI(s) extracted"
            )
        else:
            show_warning("No PSF found or incorrect format.")
        self.detection_btn.setEnabled(True)
        for i in range(len(self.viewer.layers)):
            self.viewer.layers[i].units = "µm"
            self.viewer.layers[i].scale = self.DetectionTool.pixel_size
        self.viewer.layers.selection.active = working_layer
