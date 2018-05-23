#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# Python v3 PyQt5

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X++                                               '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it         '
'  under the terms of the GNU General Public License as published by      '
' the Free Software Foundation, either version 3 of the License, or       '
' (at your option) any later version.                                     '
'                                                                         '
' cn5X++ is distributed in the hope that it will be useful, but           '
' WITHOUT ANY WARRANTY; without even the implied warranty of              '
' MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           '
' GNU General Public License for more details.                            '
'                                                                         '
' You should have received a copy of the GNU General Public License       '
' along with this program.  If not, see <http://www.gnu.org/licenses/>.   '
'                                                                         '
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from PyQt5 import QtGui, QtDesigner

# ===== adapter selon le widget! ==========================================
# nom (str) du fichier du widget sans extension
FICHIERWIDGET = "qweditmask"
# nom (str) de la classe du widget pour importer
NOMCLASSEWIDGET = "qwEditMask"
# nom (str) de l'instance dans Designer
NOMWIDGET = "qwEditMask"
# groupe (str) de widgets pour affichage dans Designer
GROUPEWIDGET = "cn5X++ widgets"
# texte (str) pour le toolTip dans Designer
TEXTETOOLTIP = "Editeur de masque 6 axes"
# texte (str) pour le whatsThis dans Designer
TEXTEWHATSTHIS = "Editeur de masque 6 axes"
# icone (rien ou un fichier image ou un QPixmap) pour afficher dans Designer
ICONEWIDGET = QtGui.QIcon()  # sans image, l'icone est celui de Qt
# ===========================================================================

# importation de la classe du widget
modulewidget = __import__(FICHIERWIDGET, fromlist=[NOMCLASSEWIDGET])
CLASSEWIDGET = getattr(modulewidget, NOMCLASSEWIDGET)

#############################################################################
class qwEditMaskPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """classe pour renseigner Designer sur le widget
       nom de classe a renommer selon le widget
    """

    #========================================================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initialized = False

    #========================================================================
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    #========================================================================
    def isInitialized(self):
        return self.initialized

    #========================================================================
    def createWidget(self, parent):
        """retourne une instance de la classe qui definit le nouveau widget
        """
        return CLASSEWIDGET(parent)

    #========================================================================
    def name(self):
        """definit le nom du widget dans QtDesigner
        """
        return NOMCLASSEWIDGET

    #========================================================================
    def group(self):
        """definit le nom du groupe de widgets dans QtDesigner
        """
        return GROUPEWIDGET

    #========================================================================
    def icon(self):
        """retourne l'icone qui represente le widget dans Designer
           => un QtGui.QIcon() ou un QtGui.QIcon(imagepixmap)
        """
        return ICONEWIDGET

    #========================================================================
    def toolTip(self):
        """retourne une courte description du widget comme tooltip
        """
        return TEXTETOOLTIP

    #========================================================================
    def whatsThis(self):
        """retourne une courte description du widget pour le "What's this?"
        """
        return TEXTEWHATSTHIS

    #========================================================================
    def isContainer(self):
        """dit si le nouveau widget est un conteneur ou pas
        """
        return False

    #========================================================================
    def domXml(self):
        """donne des proprietes du widget pour utilisation dans Designer
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

    #========================================================================
    def includeFile(self):
        """retourne le nom du fichier (str sans extension) du widget
        """
        return FICHIERWIDGET
