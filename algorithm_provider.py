from qgis.core import QgsProcessingProvider
from .herramienta import VisibilityProfileTool

class CustomAlgorithmProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(VisibilityProfileTool())

    def id(self):
        return "visibility_profile"

    def name(self):
        return "Visibility Profile Tools"

    def longName(self):
        return "Herramientas para Perfíl de Visibilidad"
		
