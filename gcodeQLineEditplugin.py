#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from PyQt5 import QtGui, QtDesigner

FICHIERWIDGET = "gcodeQLineEdit"                                        # nom (str) du fichier du widget sans extension
NOMCLASSEWIDGET = "gcodeQLineEdit"                                      # nom (str) de la classe du widget importé
NOMWIDGET = "gcodeLineEdit"                                             # nom (str) de l'instance crée dans Designer
GROUPEWIDGET = "Widget perso"                                           # groupe (str) de widgets pour Designer
TEXTETOOLTIP = "Un QLineEdit avec envoi signal keyPressed(QKeyEvent)"   # texte (str) pour le toolTip dans Designer
TEXTEWHATSTHIS = "Un QLineEdit avec envoi signal keyPressed(QKeyEvent)" # texte (str) pour le whatsThis dans Designer
ICONEWIDGET = QtGui.QIcon()                                             # (rien ou QPixmap) sans pixmap, l'icone par défaut est celui de Qt

# importation de la classe du widget
modulewidget = __import__(FICHIERWIDGET, fromlist=[NOMCLASSEWIDGET])
CLASSEWIDGET = getattr(modulewidget, NOMCLASSEWIDGET)

class gcodeQLineEditPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
  """
  classe pour renseigner Designer sur le widget
  nom de classe à renommer selon le widget
  """

  def __init__(self, parent=None):
    super(gcodeQLineEditPlugin, self).__init__(parent)
    self.initialized = False

  def initialize(self, core):
    if self.initialized:
      return
    self.initialized = True

  def isInitialized(self):
    return self.initialized

  def createWidget(self, parent):
    """
    Retourne une instance de la classe qui définit le nouveau widget
    """
    return CLASSEWIDGET(parent)

  def name(self):
    """
    Définit le nom du widget dans QtDesigner
    """
    return NOMCLASSEWIDGET

  def group(self):
    """
    Définit le nom du groupe de widgets dans QtDesigner
    """
    return GROUPEWIDGET

  def icon(self):
    """
    Retourne l'icone qui represente le widget dans Designer
    => un QtGui.QIcon() ou un QtGui.QIcon(imagepixmap)
    """
    return ICONEWIDGET

  def toolTip(self):
    """
    Retourne une courte description du widget comme tooltip
    """
    return TEXTETOOLTIP

  def whatsThis(self):
    """
    Retourne une courte description du widget pour le "What's this?"
    """
    return TEXTEWHATSTHIS

  def isContainer(self):
    """
    Dit si le nouveau widget est un conteneur ou pas
    """
    return False

  def domXml(self):
    """
    Donne des propriétés du widget pour utilisation dans Designer
    """
    return ('<widget class="{}" name="{}">\n' \
           ' <property name="toolTip" >\n' \
           '  <string>{}</string>\n' \
           ' </property>\n' \
           ' <property name="whatsThis" >\n' \
           '  <string>{}</string>\n' \
           ' </property>\n' \
           '</widget>\n'\
           ).format(NOMCLASSEWIDGET, NOMWIDGET, TEXTETOOLTIP, TEXTEWHATSTHIS)

  def includeFile(self):
    """
    Retourne le nom du fichier (str sans extension) du widget
    """
    return FICHIERWIDGET
