import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._metrics_widget import *
from unittest.mock import Mock,MagicMock

@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

def test_metrics_tool_page_initialize(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Metricstoolpage(mock_viewer)
    assert widget.viewer == mock_viewer
    assert widget.count_windows == 0
    assert widget.groupMetrics.title() == "Metrics parameters"

def test_print_results(qapp):
    mock_viewer = Mock()
    mock_viewer.layers = MagicMock()
    mock_viewer.layers.selection = MagicMock()
    mock_viewer.layers.selection.active = None
    widget = Metricstoolpage(mock_viewer)
    widget.printResults(SBR=3.14)
    expected_text = "- Signal to background ratio: 3.14"
    assert widget.resultsLabel.text() == expected_text