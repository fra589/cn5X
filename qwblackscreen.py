# -*- coding: utf-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file is part of cn5X++                                             '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
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

import sys
import threading
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings, QEvent
from PyQt5.QtGui import QKeyEvent
from gcodeQLineEdit import gcodeQLineEdit
from PyQt5.QtTest import QTest


class qwBlackScreen(QtWidgets.QWidget):
  ''' Widget personalise construisant un écran noir
  cet écran disparait en cas de click ou d'appuis sur une touche '''

  def __init__(self, parent=None):
    super().__init__()
    
    self.__txt = None

    # Initialise l'interface utilisateur du clavier
    self.parent = parent
    self.blackScreen = QtWidgets.QWidget(parent)
    self.blackScreen.setStyleSheet("background-color: black")
    self.blackScreen.setCursor(Qt.BlankCursor)
    self.blackScreen.move(0, 0)
    self.blackScreen.resize(parent.width(), parent.height())
    
    # Le l'écran noir est masqué au départ
    self.blackScreen.setVisible(False)
    
    # Connections des evennements 
    # Marche pô -( traité dans le hook global de détection d'activité


  def blackScreen_show(self):
    self.blackScreen.resize(self.parent.width(), self.parent.height())
    self.blackScreen.setVisible(True)


  def blackScreen_hide(self):
    self.blackScreen.setVisible(False)


  def isVisible(self):
    return self.blackScreen.isVisible()

