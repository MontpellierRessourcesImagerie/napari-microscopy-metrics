import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._detection_tool_widget import *
from napari_microscopy_metrics.json_utils import *
from unittest.mock import Mock,MagicMock,patch

@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

def test_Detection_parameter_widget_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = DetectionParametersWidget(mock_viewer)
    assert widget.viewer == mock_viewer

"""def test_on_confirm(qtbot,qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = DetectionToolTab(viewer=mock_viewer)
    with qtbot.capture_exceptions() as ex :
        widget.apply()
    assert not ex"""

"""def test_updates(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Detection_Parameters_Widget(viewer=mock_viewer,params=params)
    widget.updateMinDistance(123)
    assert widget.minDistanceLabel.text() == "Minimal distance :123"
    assert widget.params["Min_dist"] == 123
    widget.updateSigma(456)
    assert widget.blobSigmaLabel.text() == "Sigma : 456"
    assert widget.params["Sigma"] == 456
    widget.updateThreshold(789)
    assert widget.thresholdRelLabel.text() == "Relative threshold : 7.89"
    assert widget.params["Rel_threshold"] == 789
    widget.updateCropFactor(159)
    assert widget.cropFactorLabel.text() == "Crop factor : 159"
    assert widget.params["cropFactor"] == 159
    widget.selectedAction(2)
    assert widget.paramsStack.currentIndex() == 1
    widget._update_auto_threshold(2)
    assert widget.params["auto_threshold"] == True"""

"""def test_Detection_tool_tab_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    params = read_file_data("parameters_data.json")
    widget = Detection_Tool_Tab(mock_viewer)
    assert widget.params == params"""

def test_Detection_tool_tab_layer_removed(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = DetectionToolTab(mock_viewer)
    mock_filter_layer = Mock()
    mock_filter_layer.name = "ROI"
    mock_filtered_layer = Mock()
    mock_filtered_layer.name = "Filtered"
    mock_cropped_layer1 = Mock()
    mock_cropped_layer1.name = "Cropped1"
    mock_cropped_layer2 = Mock()
    mock_cropped_layer2.name = "Cropped2"
    widget.ROILayer = mock_filter_layer
    widget.detectedBeadsLayer = mock_filtered_layer
    mock_event = Mock()
    mock_event.value = mock_filter_layer
    widget.onLayerRemoved(mock_event)
    assert widget.ROILayer is None
    mock_event.value = mock_filtered_layer
    widget.onLayerRemoved(mock_event)
    assert widget.detectedBeadsLayer is None

def test_Detection_tool_tab_open_parameters_window(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = DetectionToolTab(mock_viewer)
    widget.openParametersWindow()
    assert widget.countWindows == 1
    widget.openParametersWindow()
    assert widget.countWindows == 1
    widget.onParametersWindowClosed({})
    assert widget.countWindows == 0

"""def test_Detection_tool_tab_on_params_updated(qapp, tmp_path):
    original_home = os.path.expanduser("~")
    os.environ["HOME"] = str(tmp_path)
    config_dir = os.path.join(tmp_path, ".napari", "microscopy_metrics")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "acquisition_data.json")
    params = {
        "Min_dist": 10,
        "Rel_threshold": 6,
        "Sigma": 3,
        "theorical_bead_size": 10,
        "cropFactor": 5,
        "selected_tool": 0,
        "auto_threshold": False,
        "rejectionZone": 10,
        "distance_annulus": 10,
        "thickness_annulus": 10,
        "threshold_choice": "otsu"
    }
    with open(config_path, 'w') as f:
        json.dump(params, f)
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Detection_Tool_Tab(mock_viewer)
    assert widget.params == params
    widget.parametersWindow = Mock()
    new_params = params.copy()
    new_params["Min_dist"] = 11
    widget.on_params_updated(new_params)
    assert widget.params == new_params"""

def test_erase_Layers(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    widget = DetectionToolTab(mock_viewer)
    mock_filter_layer = Mock()
    mock_filtered_layer = Mock()
    widget.ROILayer = mock_filter_layer
    widget.detectedBeadsLayer = mock_filtered_layer
    widget.erase_Layers()
    mock_viewer.layers.remove.assert_any_call(mock_filter_layer)
    mock_viewer.layers.remove.assert_any_call(mock_filtered_layer)
