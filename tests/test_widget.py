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
    widget = Microscopy_Metrics_QWidget(mock_viewer)
    assert widget.runButton.text() == "Run analysis"