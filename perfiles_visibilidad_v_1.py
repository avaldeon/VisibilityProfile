from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource, 
                       QgsProcessingParameterRasterLayer, QgsProcessingParameterNumber, 
                       QgsProcessingParameterFileDestination, QgsPointXY)
from qgis.core import QgsRaster, QgsRasterLayer, QgsProject, QgsGeometry, QgsFeature
import numpy as np
import matplotlib.pyplot as plt

class VisibilityProfileTool(QgsProcessingAlgorithm):
    """
    Herramienta personalizada de QGIS para calcular el perfil topográfico
    y visibilidad entre dos puntos y generar un gráfico.
    """

    # Definimos las constantes para los parámetros
    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_RASTER = 'INPUT_RASTER'
    OBSERVER_HEIGHT = 'OBSERVER_HEIGHT'
    TARGET_HEIGHT = 'TARGET_HEIGHT'
    OUTPUT_FILE = 'OUTPUT_FILE'

    def initAlgorithm(self, config=None):
        """Definir los parámetros de entrada de la herramienta."""
        
        # Capa de puntos que contiene el observador y el objetivo
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                'Capa de puntos: Debe tener un campo "tipo_punto" con valor 0 para el observador y valor 1 para el objetivo',
                [QgsProcessing.TypeVectorPoint]
            )
        )
        
        # Capa de raster (MDT)
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER,
                'MDT (Modelo Digital del Terreno)'
            )
        )
        
        # Altura del observador
        self.addParameter(
            QgsProcessingParameterNumber(
                self.OBSERVER_HEIGHT,
                'Altura del observador (m)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=2.0
            )
        )
        
        # Altura del objetivo
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TARGET_HEIGHT,
                'Altura del objetivo (m)',
                type=QgsProcessingParameterNumber.Double,
                defaultValue=120.0
            )
        )
        
        # Archivo de salida donde se guardará el gráfico
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                'Archivo de salida (gráfico de perfil)',
                fileFilter='PNG (*.png)'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Este es el método principal que se ejecuta cuando se llama a la herramienta."""
        
        # Obtener los parámetros de entrada
        points_layer = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        mdt_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        observer_height = self.parameterAsDouble(parameters, self.OBSERVER_HEIGHT, context)
        target_height = self.parameterAsDouble(parameters, self.TARGET_HEIGHT, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)
        
        # Obtener los puntos del observador y del objetivo
        observer_point, target_point = self.get_points_from_layer(points_layer)
        
        # Generar el perfil topográfico y visibilidad
        self.generate_profile(mdt_layer, observer_point, observer_height, target_point, target_height, output_file)
        
        return {self.OUTPUT_FILE: output_file}

    def get_points_from_layer(self, points_layer):
        """Obtiene los puntos del observador y del objetivo desde la capa de puntos."""
        observer_point = None
        target_point = None

        # Iteramos sobre las entidades de la capa
        for feature in points_layer.getFeatures():
            geom = feature.geometry()
            point = geom.asPoint()  # Extraer el punto
            tipo_punto = feature['tipo_punto']  # Se asume que la capa tiene un campo "tipo_punto"

            if tipo_punto == 0:  # Observador
                observer_point = QgsPointXY(point)
            elif tipo_punto == 1:  # Objetivo
                target_point = QgsPointXY(point)

        if observer_point and target_point:
            return observer_point, target_point
        else:
            raise ValueError("Faltan puntos de observador u objetivo en la capa de puntos.")

    def get_elevation_at_point(self, layer, point):
        """Devuelve la elevación de un MDT en un punto específico."""
        # Identificación del valor de elevación en el punto especificado
        result = layer.dataProvider().identify(point, 1).results()  # '1' indica el primer canal del raster
        return result.get(1, None)  # Retorna la elevación o None si no está disponible

    def generate_profile(self, layer, observer_point, observer_height, target_point, target_height, output_file):
        """Genera el perfil topográfico y calcula la visibilidad entre dos puntos."""
        
        # Cargar los puntos y trazar la línea entre ellos
        line = QgsGeometry.fromPolylineXY([observer_point, target_point])
        
        # Determinamos la resolución del MDT (tamaño de píxel)
        pixel_size_x = layer.rasterUnitsPerPixelX()
        pixel_size_y = layer.rasterUnitsPerPixelY()
        
        # Número de puntos a muestrear en la línea
        num_points = int(line.length() / max(pixel_size_x, pixel_size_y))
        
        # Generamos los puntos a lo largo de la línea con intervalos equidistantes
        total_distance = line.length()
        distances = np.linspace(0, total_distance, num_points + 1)
        
        points = [line.interpolate(d).asPoint() for d in distances]  # Puntos equidistantes

        # Obtenemos las elevaciones a lo largo de la línea
        elevations = []
        for p in points:
            elevation = self.get_elevation_at_point(layer, QgsPointXY(p))
            if elevation is not None:
                elevations.append(elevation)
            else:
                elevations.append(0)  # Si no se obtiene la elevación, se asigna 0 como valor predeterminado
        
        # Coordenadas en el espacio
        observer_z = elevations[0] + observer_height
        
        # Lista para almacenar los colores (verde, amarillo, rojo) y ángulo máximo
        colors = []
        max_angle = -np.inf  # Ángulo máximo inicial (para el terreno)

        # Cálculo de ángulos y visibilidad
        for i, (z, d) in enumerate(zip(elevations, distances)):
            if d == 0:  # El primer punto es el observador, lo tomamos como visible
                colors.append('green')
                continue
            
            # Altura real del punto en el terreno
            z_actual = z
            z_with_object = z_actual + target_height  # Altura del objeto en cada punto

            # Calculamos el ángulo entre el observador y el punto actual (suelo)
            angle = np.arctan((z_actual - observer_z) / d)

            # Caso 1: El terreno es visible
            if angle > max_angle:
                max_angle = angle  # Actualizamos el ángulo máximo SOLO con el terreno
                colors.append('green')  # El terreno es visible
            else:
                # Caso 2: El terreno no es visible, pero el objeto sí
                angle_with_object = np.arctan((z_with_object - observer_z) / d)
                if angle_with_object > max_angle:
                    colors.append('yellow')  # El objeto es visible, pero no el terreno
                else:
                    # Caso 3: Ni el terreno ni el objeto son visibles
                    colors.append('red')

        # Graficamos el perfil topográfico
        plt.figure(figsize=(10, 5))
        plt.plot(distances, elevations, label='Perfil del terreno', color='black')
        plt.fill_between(distances, elevations, observer_z, where=(np.array(colors) == 'red'), color='red', alpha=0.5)
        plt.fill_between(distances, elevations, observer_z, where=(np.array(colors) == 'yellow'), color='yellow', alpha=0.5)
        plt.fill_between(distances, elevations, observer_z, where=(np.array(colors) == 'green'), color='green', alpha=0.5)

        # Marcamos al observador y el objetivo
        plt.scatter(0, observer_z, color='blue', label='Observador (altura={})'.format(observer_height))
        plt.scatter(total_distance, elevations[-1] + target_height, color='orange', label='Objetivo (altura={})'.format(target_height))
        
        # Determinamos el color del objeto según su visibilidad
        object_angle = np.arctan((elevations[-1] + target_height - observer_z) / total_distance)
        if object_angle > max_angle:
            plt.scatter(total_distance, elevations[-1] + target_height, color='yellow')  # El objeto es visible
        else:
            plt.scatter(total_distance, elevations[-1] + target_height, color='red')  # El objeto no es visible
        
        plt.xlabel('Distancia (m)')
        plt.ylabel('Altura (m)')
        plt.legend()
        plt.title('Perfil topográfico y visibilidad (terreno y objeto)')
        plt.grid(True)

        # Guardar el gráfico en el archivo especificado
        plt.savefig(output_file)
        plt.close()

    def name(self):
        return 'visibility_profile_tool'

    def displayName(self):
        return 'Herramienta de perfil de visibilidad'

    def group(self):
        return 'Herramientas visibilidad'

    def groupId(self):
        return 'custom_tools'

    def createInstance(self):
        return VisibilityProfileTool()
