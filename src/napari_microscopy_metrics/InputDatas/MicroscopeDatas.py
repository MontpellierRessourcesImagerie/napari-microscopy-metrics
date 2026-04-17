from microscopy_metrics.resolutionTools.theoretical_resolution import TheoreticalResolution
from napari_microscopy_metrics.InputDatas.Datas import Datas

class MicroscopeDatas(Datas):
    def __init__(self, microscopeType = "widefield", numericalAperture = 1.0, emissionWavelength = 450, refractiveIndex = 1.45):
        self._microscopeType = microscopeType
        self._numericalAperture = numericalAperture
        self._emissionWavelength = emissionWavelength
        self._refractiveIndex = refractiveIndex

    def sendDatas(self, target):
        if not hasattr(target, "_TheoreticalResolutionTool"):
            raise ValueError("The target must need a _TheoreticalResolutionTool parameter !")
        else :
            target._TheoreticalResolutionTool = TheoreticalResolution.getInstance(self._microscopeType)
        if hasattr(target._TheoreticalResolutionTool, "_numericalAperture"):
            target._TheoreticalResolutionTool._numericalAperture = self._numericalAperture
        if hasattr(target._TheoreticalResolutionTool, "_emissionWavelength"):
            target._TheoreticalResolutionTool._emissionWavelength = self._emissionWavelength / 1000
        if hasattr(target._TheoreticalResolutionTool, "_refractiveIndex"):
            target._TheoreticalResolutionTool._refractiveIndex = self._refractiveIndex

    def toDict(self):
        return {
            "microscopeType": self._microscopeType,
            "numericalAperture": self._numericalAperture,
            "emissionWavelength": self._emissionWavelength,
            "refractiveIndex": self._refractiveIndex
        }