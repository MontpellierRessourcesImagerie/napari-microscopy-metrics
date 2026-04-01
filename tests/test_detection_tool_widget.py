import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._detection_tool_widget import *
from napari_microscopy_metrics.json_utils import *
from unittest.mock import Mock,MagicMock,patch

@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture
def mock_viewer():
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    yield mock_viewer

def test_Detection_parameter_widget_initialize(qapp,mock_viewer):
    widget = DetectionParametersWidget(mock_viewer)
    assert widget.viewer == mock_viewer

def test_Detection_tool_tab_layer_removed(qapp,mock_viewer):
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

def test_Detection_tool_tab_open_parameters_window(qapp,mock_viewer):
    widget = DetectionToolTab(mock_viewer)
    widget.openParametersWindow()
    assert widget.countWindows == 1
    widget.openParametersWindow()
    assert widget.countWindows == 1
    widget.onParametersWindowClosed({})
    assert widget.countWindows == 0

def test_erase_Layers(qapp,mock_viewer):
    widget = DetectionToolTab(mock_viewer)
    mock_filter_layer = Mock()
    mock_filtered_layer = Mock()
    widget.ROILayer = mock_filter_layer
    widget.detectedBeadsLayer = mock_filtered_layer
    widget.erase_Layers()
    mock_viewer.layers.remove.assert_any_call(mock_filter_layer)
    mock_viewer.layers.remove.assert_any_call(mock_filtered_layer)
