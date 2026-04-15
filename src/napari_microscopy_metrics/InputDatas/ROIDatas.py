from napari_microscopy_metrics.InputDatas.Datas import Datas

class ROIDatas(Datas):
    def __init__(self, beadSize = 0.6, rejectionDistance = 0.5, ringInnerDistance = 1.0, ringThickness = 2.0, cropFactor = 5, thresholdIntensity = 0.95):
        self._beadSize = beadSize
        self.rejectionDistance = rejectionDistance
        self._ringInnerDistance = ringInnerDistance
        self._ringThickness = ringThickness
        self._cropFactor = cropFactor
        self._thresholdIntensity = thresholdIntensity

    def sendDatas(self, target):
        if hasattr(target, "_beadSize"):
            target._beadSize = self._beadSize
        if hasattr(target, "_rejectionDistance"):
            target._rejectionDistance = self.rejectionDistance
        if hasattr(target, "_cropFactor"): 
            target._cropFactor = self._cropFactor
        if hasattr(target, "_thresholdIntensity"):
            target._thresholdIntensity = self._thresholdIntensity
        if hasattr(target, "_ringInnerDistance"):
            target._ringInnerDistance = self._ringInnerDistance
        if hasattr(target, "_ringThickness"):
            target._ringThickness = self._ringThickness
        