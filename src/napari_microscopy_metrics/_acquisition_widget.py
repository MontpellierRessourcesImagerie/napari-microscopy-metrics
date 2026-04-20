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

        self.acquisitionGroup = QGroupBox("Image parameters")
        self.groupLayout = QVBoxLayout()
        self.acquisitionGroup.setLayout(self.groupLayout)
        self.pixelSizeLayout = QVBoxLayout()
        self.lblPixelSize = QLabel("Enter pixel size (µm/px)")
        self.lblPixelSize.setStyleSheet("font-weight: bold")
        self.lblPixelSize.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )

        self.widgetPxS = ImageSizeWidget(self.viewer)
        self.onLayerChanged()
        self.pixelSizeLayout.addWidget(self.lblPixelSize)
        self.pixelSizeLayout.addWidget(self.widgetPxS)
        self.groupLayout.addLayout(self.pixelSizeLayout)

        self.groupLayout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )

        self.microscopeLayout = QVBoxLayout()
        self.titleOptionsMicroscope = QLabel("Microscope parameters:")
        self.titleOptionsMicroscope.setStyleSheet("font-weight: bold")
        self.titleOptionsMicroscope.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Fixed
        )

        self.widgetMicroChoice = MicroscopeParametersWidget(self.viewer)
        self.microscopeLayout.addWidget(self.titleOptionsMicroscope)
        self.microscopeLayout.addWidget(self.widgetMicroChoice)
        self.groupLayout.addLayout(self.microscopeLayout)

        self.groupLayout.addWidget(self.labelShape)

        layout.addWidget(self.acquisitionGroup)
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
