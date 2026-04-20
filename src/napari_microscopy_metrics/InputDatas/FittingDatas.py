from napari_microscopy_metrics.InputDatas.Datas import Datas


class FittingDatas(Datas):
    """Class for handling fitting-related data in the napari microscopy metrics plugin."""

    def __init__(
        self, fitType="1D", thresholdRSquared=0.95, prominenceRel=0.5
    ):
        self._fitType = fitType
        self._thresholdRSquared = thresholdRSquared
        self._prominenceRel = prominenceRel

    def sendDatas(self, target):
        """Send the fitting data to the target object. The target object is expected to have a _fitType attribute that can be set with the provided fitting type, threshold R-squared, and prominence values.

        Args:
            target (BaseWidget): The object to which the fitting data will be sent.
        """
        if hasattr(target, "fitType"):
            target.fitType = self._fitType
        if hasattr(target, "_thresholdRSquared"):
            target._thresholdRSquared = self._thresholdRSquared
        if hasattr(target, "_prominenceRel"):
            target._prominenceRel = self._prominenceRel

    def toDict(self):
        """Convert the fitting data to a dictionary format for easier handling and storage.a

        Returns:
            dict: A dictionary containing the fitting data.
        """
        return {
            "fitType": self._fitType,
            "thresholdRSquared": self._thresholdRSquared,
            "prominenceRel": self._prominenceRel,
        }
