from napari_microscopy_metrics.InputDatas.Datas import Datas


class ROIDatas(Datas):
    """Class for handling region of interest (ROI)-related data in the napari microscopy metrics plugin."""

    def __init__(
        self,
        beadSize=0.6,
        rejectionDistance=0.5,
        ringInnerDistance=1.0,
        ringThickness=2.0,
        cropFactor=5,
        thresholdIntensity=0.95,
    ):
        self._beadSize = beadSize
        self._rejectionDistance = rejectionDistance
        self._ringInnerDistance = ringInnerDistance
        self._ringThickness = ringThickness
        self._cropFactor = cropFactor
        self._thresholdIntensity = thresholdIntensity

    def sendDatas(self, target):
        """Send the ROI data to the target object. The target object is expected to have attributes that can be set with the provided ROI values.

        Args:
            target (BaseWidget): The object to which the ROI data will be sent.
        """
        if hasattr(target, "_beadSize"):
            target._beadSize = self._beadSize
        if hasattr(target, "_rejectionDistance"):
            target._rejectionDistance = self._rejectionDistance
        if hasattr(target, "_cropFactor"):
            target._cropFactor = self._cropFactor
        if hasattr(target, "_thresholdIntensity"):
            target._thresholdIntensity = self._thresholdIntensity
        if hasattr(target, "_ringInnerDistance"):
            target._ringInnerDistance = self._ringInnerDistance
        if hasattr(target, "_ringThickness"):
            target._ringThickness = self._ringThickness

    def toDict(self):
        """Convert the ROI data to a dictionary format for easier handling and storage.

        Returns:
            dict: A dictionary containing the ROI data.
        """
        return {
            "beadSize": self._beadSize,
            "rejectionDistance": self._rejectionDistance,
            "ringInnerDistance": self._ringInnerDistance,
            "ringThickness": self._ringThickness,
            "cropFactor": self._cropFactor,
            "thresholdIntensity": self._thresholdIntensity,
        }
