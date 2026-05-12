from microscopy_metrics.resolutionTools.theoretical_resolution import (
    TheoreticalResolution,
)
from napari_microscopy_metrics.InputDatas.Datas import Datas


class MicroscopeDatas(Datas):
    """Class for handling microscope-related data in the napari microscopy metrics plugin."""

    def __init__(
        self,
        microscopeType="widefield",
        numericalAperture=1.0,
        emissionWavelength=450,
        refractiveIndex=1.45,
        excitationWavelength=225
    ):
        self._microscopeType = microscopeType
        self._numericalAperture = numericalAperture
        self._emissionWavelength = emissionWavelength
        self._refractiveIndex = refractiveIndex
        self._excitationWavelength = excitationWavelength

    def sendDatas(self, target):
        """Send the microscope data to the target object. The target object is expected to have a _TheoreticalResolutionTool attribute that can be set with the provided microscope type, numerical aperture, emission wavelength, and refractive index values.

        Args:
            target (BaseWidget): The object to which the microscope data will be sent.
        Raises:
            ValueError: If the target object does not have a _TheoreticalResolutionTool attribute.
        """
        if not hasattr(target, "_TheoreticalResolutionTool"):
            raise ValueError(
                "The target must need a _TheoreticalResolutionTool parameter !"
            )
        else:
            target._TheoreticalResolutionTool = (
                TheoreticalResolution.getInstance(self._microscopeType)
            )
        if hasattr(target._TheoreticalResolutionTool, "_numericalAperture"):
            target._TheoreticalResolutionTool._numericalAperture = (
                self._numericalAperture
            )
        if hasattr(target._TheoreticalResolutionTool, "_emissionWavelength"):
            target._TheoreticalResolutionTool._emissionWavelength = (
                self._emissionWavelength / 1000
            )
        if hasattr(target._TheoreticalResolutionTool, "_refractiveIndex"):
            target._TheoreticalResolutionTool._refractiveIndex = (
                self._refractiveIndex
            )
        if hasattr(target._TheoreticalResolutionTool, "_excitationWavelength"):
            target._TheoreticalResolutionTool._excitationWavelength = self._excitationWavelength

    def toDict(self):
        """Convert the microscope data to a dictionary format for easier handling and storage.
        Returns:
            dict: A dictionary containing the microscope data.
        """
        return {
            "microscopeType": self._microscopeType,
            "numericalAperture": self._numericalAperture,
            "emissionWavelength": self._emissionWavelength,
            "refractiveIndex": self._refractiveIndex,
            "excitationWavelength": self._excitationWavelength
        }
