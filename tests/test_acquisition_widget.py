import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._acquisition_widget import *
from unittest.mock import Mock,MagicMock

@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

def test_acquisition_page_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Acquisition_tool_page(mock_viewer)
    assert widget.viewer == mock_viewer
    assert widget.count_windows == 0
    assert widget.params["PhysicSizeX"] == 0.06
    assert widget.title.text() == "Image parameters"

def test_on_layer_changed_with_active_layer(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_layer = MagicMock(spec=napari.layers.Image)
    mock_layer.data = np.zeros((10,5,20))
    mock_viewer.layers.selection.active = mock_layer
    widget = Acquisition_tool_page(mock_viewer)
    widget._on_layer_changed()
    assert widget.params["ShapeZ"] == 10
    assert widget.params["ShapeY"] == 5
    assert widget.params["ShapeX"] == 20
    assert widget.label_shape.text() == "20 x 5 x 10 px"

def test_on_layer_changed_without_active_layer(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Acquisition_tool_page(mock_viewer)
    widget._on_layer_changed()
    assert widget.label_shape.text() == ""

def test_on_apply(qapp, tmp_path):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Acquisition_tool_page(mock_viewer)
    original_home = os.path.expanduser("~")
    os.environ["HOME"] = str(tmp_path)
    widget._on_apply()
    config_path = os.path.join(tmp_path, ".napari", "microscopy_metrics", "acquisition_data.json")
    assert os.path.exists(config_path)
    with open(config_path, "r") as f:
        saved_params = json.load(f)
    assert saved_params == widget.params
    os.environ["HOME"] = original_home

def test_signal_connection(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.events = MagicMock()
    mock_viewer.layers.selection.events.active = MagicMock()
    widget = Acquisition_tool_page(mock_viewer)
    mock_viewer.layers.selection.events.active.connect.assert_called_once_with(widget._on_layer_changed)

