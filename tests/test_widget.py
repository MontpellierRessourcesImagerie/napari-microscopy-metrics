import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._widget import *
from napari_microscopy_metrics.json_utils import *
from unittest.mock import Mock,MagicMock,patch

def test_widget_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    params = read_file_data("parameters_data.json")
    parameters_acquisition = read_file_data("acquisition_data.json")
    widget = Microscopy_Metrics_QWidget(mock_viewer)
    assert widget.parameters_detection == params
    assert widget.parameters_acquisition == parameters_acquisition