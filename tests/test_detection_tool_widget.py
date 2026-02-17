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
    params = read_file_data("parameters_data.json")
    widget = Detection_Parameters_Widget(mock_viewer, params)
    assert widget.viewer == mock_viewer
    assert widget.params == params

def test_on_confirm(qtbot,qapp):
    params = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
            "theorical_bead_size":10,
            "crop_factor":5,
            "selected_tool":0,
            "auto_threshold":False,
            "rejection_zone":10,
            "distance_annulus" : 10,
            "thickness_annulus": 10,
            "threshold_choice":"otsu"
        }
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Detection_Parameters_Widget(viewer=mock_viewer,params=params)
    with qtbot.capture_exceptions() as ex :
        widget._on_confirm()
    assert not ex
    assert "theorical_bead_size" in widget.params

def test_updates(qapp):
    params = {
            "Min_dist":10,
            "Rel_threshold":6,
            "Sigma":3,
            "theorical_bead_size":10,
            "crop_factor":5,
            "selected_tool":0,
            "auto_threshold":False,
            "rejection_zone":10,
            "distance_annulus" : 10,
            "thickness_annulus": 10,
            "threshold_choice":"otsu"
        }
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Detection_Parameters_Widget(viewer=mock_viewer,params=params)
    widget._update_min_distance(123)
    assert widget.min_distance_label.text() == "Minimal distance :123"
    assert widget.params["Min_dist"] == 123
    widget._update_sigma(456)
    assert widget.blob_sigma_label.text() == "Sigma : 456"
    assert widget.params["Sigma"] == 456
    widget._update_threshold(789)
    assert widget.threshold_rel_label.text() == "Relative threshold : 7.89"
    assert widget.params["Rel_threshold"] == 789
    widget._update_crop_factor(159)
    assert widget.crop_factor_label.text() == "Crop factor : 159"
    assert widget.params["crop_factor"] == 159
    widget._selected_action(2)
    assert widget.params_stack.currentIndex() == 1
    widget._update_auto_threshold(2)
    assert widget.params["auto_threshold"] == True

def test_Detection_tool_tab_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    params = read_file_data("parameters_data.json")
    widget = Detection_Tool_Tab(mock_viewer)
    assert widget.params == params

def test_Detection_tool_tab_layer_removed(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    params = read_file_data("parameters_data.json")
    widget = Detection_Tool_Tab(mock_viewer)
    mock_filter_layer = Mock()
    mock_filter_layer.name = "ROI"
    mock_filtered_layer = Mock()
    mock_filtered_layer.name = "Filtered"
    mock_cropped_layer1 = Mock()
    mock_cropped_layer1.name = "Cropped1"
    mock_cropped_layer2 = Mock()
    mock_cropped_layer2.name = "Cropped2"
    widget.filter_layer = mock_filter_layer
    widget.filtered_layer = mock_filtered_layer
    widget.cropped_layers = [mock_cropped_layer1,mock_cropped_layer2]
    mock_event = Mock()
    mock_event.value = mock_filter_layer
    widget._on_layer_removed(mock_event)
    assert widget.filter_layer is None
    mock_event.value = mock_filtered_layer
    widget._on_layer_removed(mock_event)
    assert widget.filtered_layer is None
    mock_event.value = mock_cropped_layer1
    widget._on_layer_removed(mock_event)
    assert mock_cropped_layer1 not in widget.cropped_layers
    assert mock_cropped_layer2 in widget.cropped_layers

def test_Detection_tool_tab_open_parameters_window(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    params = read_file_data("parameters_data.json")
    widget = Detection_Tool_Tab(mock_viewer)
    widget._open_parameters_window()
    assert widget.count_windows == 1
    widget._open_parameters_window()
    assert widget.count_windows == 1
    widget._on_parameters_window_closed({})
    assert widget.count_windows == 0

def test_Detection_tool_tab_on_params_updated(qapp, tmp_path):
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
        "crop_factor": 5,
        "selected_tool": 0,
        "auto_threshold": False,
        "rejection_zone": 10,
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
    widget.parameters_window = Mock()
    new_params = params.copy()
    new_params["Min_dist"] = 11
    widget.on_params_updated(new_params)
    assert widget.params == new_params

def test_erase_Layers(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    widget = Detection_Tool_Tab(mock_viewer)
    mock_filter_layer = Mock()
    mock_filtered_layer = Mock()
    widget.filter_layer = mock_filter_layer
    widget.filtered_layer = mock_filtered_layer
    widget.erase_Layers()
    mock_viewer.layers.remove.assert_any_call(mock_filter_layer)
    mock_viewer.layers.remove.assert_any_call(mock_filtered_layer)
