from napari_microscopy_metrics.InputDatas.Datas import Datas

class SizeDatas(Datas):
    def __init__(self, sizeX = 0.069, sizeY = 0.069, sizeZ = 0.1):
        self._pixelSize = [sizeZ,sizeY,sizeX]

    def sendDatas(self, target):
        if hasattr(target, "_pixelSize"):
            target._pixelSize = self._pixelSize