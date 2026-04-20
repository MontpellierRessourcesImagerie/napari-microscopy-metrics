class Datas(object):
    """Base class for all data types used in the napari microscopy metrics plugin.
    Subclasses should implement the sendDatas and toDict methods according to their specific data structure and requirements.
    """

    def sendDatas(self, target):
        pass

    def toDict(self):
        pass
