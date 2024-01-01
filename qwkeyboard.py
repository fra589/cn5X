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
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings

import qwKeyboard_ui

class qwKeyboard(QtWidgets.QWidget):
  ''' Widget personalise construisant le clavier touch screen
  '''

  def __init__(self, parent=None):
    super().__init__()
    
    self.__txt = None

    # Initialise l'interface utilisateur du clavier
    self.keyboard = QtWidgets.QFrame(parent)
    self.keyboard.setStyleSheet(".QFrame{background-color: rgba(192, 192, 192, 192); border: 1px solid #000060; margin: 0px; padding: 0px;}")
    self.keyboard.move(5, 265)
    self.keyboard.ui = qwKeyboard_ui.Ui_keyboard()
    self.keyboard.ui.setupUi(self.keyboard)
    # Le clavier est masqué au départ
    self.keyboard.setVisible(False)

    # Connections des evennements clavier
    self.keyboard.ui.keybButtonHideL.pressed.connect(self.keyboard_hide)    
    self.keyboard.ui.keybButtonHideR.pressed.connect(self.keyboard_hide)    

  def setLinkedTxt(self, txt):
    self.__txt = txt


  def keyboard_show(self):
    self.keyboard.setVisible(True)


  def keyboard_hide(self):
    self.keyboard.setVisible(False)


  def isVisible(self):
    return self.keyboard.isVisible()




