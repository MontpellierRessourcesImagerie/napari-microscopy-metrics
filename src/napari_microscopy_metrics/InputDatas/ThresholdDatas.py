from napari_microscopy_metrics.InputDatas.Datas import Datas
from microscopy_metrics.thresholdTools.threshold_tool import Threshold


class ThresholdDatas(Datas):
    """Class for handling threshold-related data in the napari microscopy metrics plugin."""

    def __init__(self, thresholdTool="manual", thresholdRel=0.5):
        self._thresholdTool = thresholdTool
        self._thresholdRel = thresholdRel

    def sendDatas(self, target):
        """Send the threshold data to the target object. The target object is expected to have a _thresholdTool attribute that can be set with the provided threshold values.

        Args:
            target (BaseWidget): The object to which the threshold data will be sent.
        """
        if not hasattr(target, "_thresholdTool"):
            raise ValueError(
                "The target must need a _thresholdTool parameter !"
            )
        else:
            target._thresholdTool = Threshold.getInstance(self._thresholdTool)
        if hasattr(target._thresholdTool, "_relThreshold"):
            target._thresholdTool._relThreshold = self._thresholdRel

    def toDict(self):
        """Convert the threshold data to a dictionary format for easier handling and storage.

        Returns:
            dict: A dictionary containing the threshold data.
        """
        return {
            "thresholdTool": self._thresholdTool,
            "thresholdRel": self._thresholdRel,
        }
