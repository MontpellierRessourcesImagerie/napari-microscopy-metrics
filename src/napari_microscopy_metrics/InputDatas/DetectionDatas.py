from napari_microscopy_metrics.InputDatas.Datas import Datas
from microscopy_metrics.detectionTools.detection_tool import DetectionTool

class DetectionDatas(Datas):
    def __init__(self, detectionTool = "peak local maxima", minDist = 1, sigma = 3):
        self._detectionTool = detectionTool
        self._minDist = minDist
        self._sigma = sigma

    def sendDatas(self,target):
        if not hasattr(target, "_detectionTool"):
            raise ValueError("The target must need a _detectionTool parameter !")
        else : 
            target._detectionTool = DetectionTool.getInstance(self._detectionTool)
        if hasattr(target._detectionTool, "minDistance"):
            target._detectionTool.minDistance = self._minDist
        if hasattr(target._detectionTool, "_sigma"):
            target._detectionTool._sigma = self._sigma

    

