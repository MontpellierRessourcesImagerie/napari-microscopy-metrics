import napari
from qtpy.QtWidgets import QWidget
from autooptions import Options


class BaseWidget(QWidget):
    """A generic base widget for options-based widgets.
    
    Attributes:
        viewer (napari.viewer.Viewer): The napari viewer instance.
        options (Options): The options object for storing and loading widget parameters.
        optionsSliders (Options): The options object for storing and loading slider parameters.
        widget (QWidget): The main widget containing the layout and controls.
        btnDoc (QPushButton): A button to open the documentation web page.
    """

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
        Must be implemented by subclasses if slider functionality is needed.
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
