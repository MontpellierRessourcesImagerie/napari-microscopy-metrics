from napari_microscopy_metrics.InputDatas.Datas import Datas

class FittingDatas(Datas):
    def __init__(self, fitType = "1D", thresholdRSquared = 0.95, prominenceRel = 0.5):
        self._fitType = fitType
        self._thresholdRSquared = thresholdRSquared
        self._prominenceRel = prominenceRel
        
    def sendDatas(self, target):
        if hasattr(target, "fitType"):
            target.fitType = self._fitType
        if hasattr(target, "_thresholdRSquared"):
            target._thresholdRSquared = self._thresholdRSquared
        if hasattr(target, "_prominenceRel"):
            target._prominenceRel = self._prominenceRel
            
