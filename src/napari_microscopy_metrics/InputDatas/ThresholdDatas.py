from napari_microscopy_metrics.InputDatas.Datas import Datas
from microscopy_metrics.thresholdTools.threshold_tool import Threshold

class ThresholdDatas(Datas):
    def __init__(self, thresholdTool = "manual", thresholdRel = 0.5):
        self._thresholdTool = thresholdTool
        self._thresholdRel = thresholdRel

    def sendDatas(self, target):
        if not hasattr(target, "_thresholdTool"):
            raise ValueError("The target must need a _thresholdTool parameter !")
        else :
            target._thresholdTool = Threshold.getInstance(self._thresholdTool)
        if hasattr(target._thresholdTool, "_relThreshold"):
            target._thresholdTool._relThreshold = self._thresholdRel

    def toDict(self):
        return {
            "thresholdTool": self._thresholdTool,
            "thresholdRel": self._thresholdRel
        }
