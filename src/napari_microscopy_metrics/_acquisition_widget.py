import napari

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
)

from napari_microscopy_metrics.widgets.ImageSizeWidget import ImageSizeWidget
from napari_microscopy_metrics.widgets.MicroscopeParametersWidget import (
    MicroscopeParametersWidget,
)


class AcquisitionToolPage(QWidget):
    """A napari widget form for microscope acquisition parameters.
    It contains an ImageSizeWidget for setting scale informations and a MicroscopeParametersWidget for setting microscope informations.
    It also update scale informations in detection widget and napari viewer when applying a new scale.
    Args:
        viewer (napari.viewer.Viewer): The environment where the widget will be displayed
    """

    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self.viewer = viewer
        self.countWindows = 0
        self.labelShape = QLabel()
        self.initUi()
        self.viewer.layers.selection.events.active.connect(self.onLayerChanged)

    def initUi(self):
        """A method to initialize the widget interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.pixelSizeGroup = QGroupBox("Pixel size parameters")
        self.pixelGroupLayout = QVBoxLayout()
        self.pixelSizeGroup.setLayout(self.pixelGroupLayout)
        self.pixelSizeWidget = ImageSizeWidget(self.viewer)
        self.lblPixelSize = QLabel("Enter pixel size (µm/px)")
        self.lblPixelSize.setStyleSheet("font-weight: bold")
        self.lblPixelSize.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )
        self.pixelGroupLayout.addWidget(self.lblPixelSize)
        self.pixelGroupLayout.addWidget(self.pixelSizeWidget)

        layout.addWidget(self.pixelSizeGroup)

        self.microscopeGroup = QGroupBox("Microscope parameters")
        self.microscopeGroupLayout = QVBoxLayout()
        self.microscopeGroup.setLayout(self.microscopeGroupLayout)
        self.microscopeWidget = MicroscopeParametersWidget(self.viewer)
        self.microscopeGroupLayout.addWidget(self.microscopeWidget)

        layout.addWidget(self.microscopeGroup)

        self.setLayout(layout)

    def onLayerChanged(self):
        """A method called when changing active layer.
        It update scale informations in detection widget if the new active layer is an image and update label with the shape of the new active image.
        """
        currentLayer = self.viewer.layers.selection.active
        if currentLayer is None or not isinstance(
            currentLayer, napari.layers.Image
        ):
            return
        image = currentLayer.data
        shape = image.shape
        self.labelShape.setText(
            f"Selected image shape : {shape[2]} x {shape[1]} x {shape[0]} px"
        )
