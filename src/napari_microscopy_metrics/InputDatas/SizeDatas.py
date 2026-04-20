from napari_microscopy_metrics.InputDatas.Datas import Datas


class SizeDatas(Datas):
    """Class for handling size-related data in the napari microscopy metrics plugin."""

    def __init__(self, sizeX=0.069, sizeY=0.069, sizeZ=0.1):
        self._pixelSize = [sizeZ, sizeY, sizeX]

    def sendDatas(self, target):
        """Send the size data to the target object. The target object is expected to have a _pixelSize attribute that can be set with the provided size values.

        Args:
            target (BaseWidget): The object to which the size data will be sent.
        """
        if hasattr(target, "_pixelSize"):
            target._pixelSize = self._pixelSize

    def toDict(self):
        """Convert the size data to a dictionary format for easier handling and storage.

        Returns:
            dict: A dictionary containing the size data.
        """
        return {
            "sizeX": self._pixelSize[2],
            "sizeY": self._pixelSize[1],
            "sizeZ": self._pixelSize[0],
        }
