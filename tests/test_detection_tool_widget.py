import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._detection_tool_widget import *
from unittest.mock import Mock,MagicMock

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