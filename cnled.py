# -*- coding: UTF-8 -*-

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

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import cn5X_rc

class cnLed(QtWidgets.QLabel):
  ''' QLabel affichant une image de Led eteinte ou allumee '''

  statusChanged = pyqtSignal(bool) # signal emis a chaque changement de valeur

  def __init__(self, parent=None):
    super(cnLed, self).__init__(parent=parent)

    self.__couleur = "Rouge" # Rouge ou Verte
    
    # Chemin des images dans le fichier de resources
    self.__imagePath = ":/cn5X/images/"
    self.iconOff = QtGui.QPixmap(self.__imagePath + "led" + self.__couleur + "Eteinte.svg")
    self.iconOn  = QtGui.QPixmap(self.__imagePath + "led" + self.__couleur + "Alumee.svg")

    # Proprietes du label
    self.setMaximumSize(QtCore.QSize(20, 20))
    self.setText("")
    self.setPixmap(self.iconOff)
    self.setScaledContents(True)

    self.__ledStatus = False # led eteinte a l'initialisation


  @pyqtSlot()
  def Couleur(self):
    return self.__couleur

    
  @pyqtSlot()
  def setCouleur(self, couleur):
    if self.__couleur != couleur:
      self.__couleur = couleur
      self.iconOff = QtGui.QPixmap(self.__imagePath + "led" + self.__couleur + "Eteinte.svg")
      self.iconOn  = QtGui.QPixmap(self.__imagePath + "led" + self.__couleur + "Alumee.svg")
      if self.__ledStatus:
        self.setPixmap(self.iconOn)
      else:
        self.setPixmap(self.iconOff)
    

  @pyqtSlot()
  def ledStatus(self):
    ''' Renvoie le status de la Led '''
    return self.__ledStatus


  @pyqtSlot(bool)
  def setLedStatus(self, s: bool):
    ''' Allume (s=True) ou eteind (s=False) la Led '''
    if self.__ledStatus != s:
      if s:
        self.setPixmap(self.iconOn)
      else:
        self.setPixmap(self.iconOff)
      self.__ledStatus = s
      self.statusChanged.emit(s)


  # Definie les propriétés pour permettre la configuration par Designer
  ledStatus = QtCore.pyqtProperty("bool", fget=ledStatus, fset=setLedStatus)
  Couleur = QtCore.pyqtProperty("QString", fget=Couleur, fset=setCouleur)
