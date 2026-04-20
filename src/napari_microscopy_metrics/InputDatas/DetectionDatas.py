from napari_microscopy_metrics.InputDatas.Datas import Datas
from microscopy_metrics.detectionTools.detection_tool import DetectionTool


class DetectionDatas(Datas):
    """Class for handling detection-related data in the napari microscopy metrics plugin."""

    def __init__(self, detectionTool="peak local maxima", minDist=1, sigma=3):
        self._detectionTool = detectionTool
        self._minDist = minDist
        self._sigma = sigma

    def sendDatas(self, target):
        """Send the detection data to the target object. The target object is expected to have a _detectionTool attribute that can be set with the provided detection tool, minimum distance, and sigma values.

        Args:
            target (BaseWidget): The object to which the detection data will be sent.

        Raises:
            ValueError: If the target object does not have a _detectionTool attribute.
        """
        if not hasattr(target, "_detectionTool"):
            raise ValueError(
                "The target must need a _detectionTool parameter !"
            )
        else:
            target._detectionTool = DetectionTool.getInstance(
                self._detectionTool
            )
        if hasattr(target._detectionTool, "minDistance"):
            target._detectionTool.minDistance = self._minDist
        if hasattr(target._detectionTool, "_sigma"):
            target._detectionTool._sigma = self._sigma

    def toDict(self):
        """Convert the detection data to a dictionary format for easier handling and storage.a

        Returns:
            dict: A dictionary containing the detection data.
        """
        return {
            "detectionTool": self._detectionTool,
            "minDist": self._minDist,
            "sigma": self._sigma,
        }
