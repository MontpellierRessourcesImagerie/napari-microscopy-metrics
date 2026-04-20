import napari
from qtpy.QtWidgets import QWidget
from autooptions import Options


class BaseWidget(QWidget):
    """A generic base widget for options-based widgets."""

    def __init__(self, viewer: "napari.viewer.Viewer", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.viewer = viewer
        self.options = self.getOptions()
        self.optionsSliders = self.getSliders()
        self.widget = None
        self.btnDoc = None
        self.createLayout()

    def createLayout(self):
        pass

    @classmethod
    def getOptions(cls) -> Options:
        """
        Create and load options.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement getOptions()")

    def getSliders(self) -> Options:
        """
        Create and load sliders options.
        Must be implemented by subclasses.
        """
        pass

    def openDocumentation(self):
        """
        Open the documentation web page.
        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement openDocumentation()"
        )

    def createDatas(self):
        pass
