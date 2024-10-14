# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VisibilityProfile
                                 A QGIS plugin
 This plugin make images with a graph drawing a profile between two points (the observer and the observed feature) and the visibility between these two points at the highest point of them
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-10-11
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Aitor Valdeón - Forestalia Renovables S.L.
        email                : avaldeon@forestalia.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import (QgsApplication, QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource, 
                       QgsProcessingParameterRasterLayer, QgsProcessingParameterNumber, 
                       QgsProcessingParameterFileDestination, QgsPointXY)
from qgis.core import QgsRaster, QgsRasterLayer, QgsProject, QgsGeometry, QgsFeature
import processing
#from qgis.gui import QgsProcessingDialog
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .visibility_profile_dialog import VisibilityProfileDialog
import os.path
import numpy as np
import matplotlib.pyplot as plt
from .herramienta import VisibilityProfileTool
from .algorithm_provider import CustomAlgorithmProvider
		
class VisibilityProfile:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'VisibilityProfile_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Visibility Profile')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.provider = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('VisibilityProfile', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

       # icon_path = ':/plugins/visibility_profile/icon.png'
        #self.add_action(
        #    icon_path,
        #    text=self.tr(u'Visibility Profile'),
        #    callback=self.run,
        #    parent=self.iface.mainWindow())

        # will be set False in run()
        #self.first_start = True
        # Inicializamos el proveedor de algoritmos solo si no existe
        self.provider = CustomAlgorithmProvider()
        # Añadimos el proveedor al registro de algoritmos de QGIS
        if not QgsApplication.processingRegistry().providerById(self.provider.id()):
            QgsApplication.processingRegistry().addProvider(self.provider)
		
        self.action = QAction(
            QIcon(os.path.join(self.plugin_dir, "icon.png")),
            "Ejecutar Herramienta",
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)  # Conecta el evento del botón a la función run
        self.iface.addToolBarIcon(self.action)  # Agrega el icono de la acción a la barra de herramientas



    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Visibility Profile'),
                action)
            self.iface.removeToolBarIcon(action)
        if self.action is not None:
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        # Elimina el proveedor de algoritmos al desactivar el plugin
        QgsApplication.processingRegistry().removeProvider(self.provider)


    def run(self):
        """Run method that performs all the real work"""

        '''# Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = VisibilityProfileDialog()

        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            VisibilityProfileTool.processAlgorithm()
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            # pass'''
        # Crea una instancia de tu herramienta
        herramienta = VisibilityProfileTool()

        # Ejecutar la herramienta usando el cuadro de diálogo estándar
        processing.execAlgorithmDialog(herramienta.id())

        '''# Recupera los parámetros por defecto de la herramienta
        params = herramienta.createParameters()  # Obtiene los parámetros predeterminados

        # Ajusta los parámetros según tus necesidades
        # params['parametro1'] = 10  # Cambia este valor según lo que necesites

        # Inicializa un objeto de feedback para manejar el progreso
        feedback = QgsProcessingFeedback()

        # Ejecuta la herramienta
        try:
            result = herramienta.run(params, feedback)  # Ejecuta la herramienta
            if result:
                self.iface.messageBar().pushMessage("Éxito", "La herramienta se ejecutó correctamente.")
            else:
                self.iface.messageBar().pushMessage("Error", "La herramienta no se ejecutó correctamente.", level=Qgis.Critical)
        except Exception as e:
            self.iface.messageBar().pushMessage("Error", str(e), level=Qgis.Critical)	'''