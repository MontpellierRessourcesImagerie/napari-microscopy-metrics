import pytest
from qtpy.QtWidgets import QApplication
from napari_microscopy_metrics._acquisition_widget import *
from unittest.mock import Mock,MagicMock
import numpy as np

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

def test_acquisition_page_initialize(qapp,mock_viewer):
    widget = AcquisitionToolPage(mock_viewer)
    assert widget.viewer == mock_viewer
    assert widget.countWindows == 0
    assert widget.pixelSizeGroup.title() == "Pixel size parameters"

def test_on_layer_changed_with_active_layer(qapp,mock_viewer):
    mock_layer = MagicMock(spec=napari.layers.Image)
    mock_layer.data = np.zeros((10,5,20))
    mock_viewer.layers.selection.active = mock_layer
    widget = AcquisitionToolPage(mock_viewer)
    widget.onLayerChanged()
    assert widget.labelShape.text() == "Selected image shape : 20 x 5 x 10 px"

def test_on_layer_changed_without_active_layer(qapp,mock_viewer):
    widget = AcquisitionToolPage(mock_viewer)
    widget.onLayerChanged()
    assert widget.labelShape.text() == ""

def test_signal_connection(qapp,mock_viewer):
    mock_viewer.layers.selection.events = MagicMock()
    mock_viewer.layers.selection.events.active = MagicMock()
    widget = AcquisitionToolPage(mock_viewer)
    mock_viewer.layers.selection.events.active.connect.assert_called_once_with(widget.onLayerChanged)

