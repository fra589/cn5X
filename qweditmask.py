# -*- coding: utf-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, pyqtProperty
from PyQt6.QtGui import QIntValidator

class qwEditMask(QtWidgets.QWidget):
  ''' Widget personalise construisant un masque binaire (pour 6 axes) avec 6 cases a cocher
  '''

  valueChanged = pyqtSignal(int) # signal emis a chaque changement de valeur

  def __init__(self, parent=None):
    super().__init__(parent)

    self.__changeEnCours = False
    self.__nbAxes = 6

    # Creation cadre exterieur
    self.frame = QtWidgets.QFrame()
    self.frame.setMinimumSize(QSize(127, 19))
    self.frame.setMaximumSize(QSize(127, 19))
    self.frame.setObjectName("frame")
    self.horizontalLayout = QtWidgets.QHBoxLayout(self.frame)
    self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
    self.horizontalLayout.setSpacing(2)
    self.horizontalLayout.setObjectName("horizontalLayout")

    # creation des 6 checkBoxes
    self.chk = []
    for i in range(6):
      self.chk.append(QtWidgets.QCheckBox(self.frame))
      self.chk[i].setLayoutDirection(Qt.LayoutDirection.RightToLeft)
      self.chk[i].setText("")
      self.chk[i].setObjectName("chk{}".format(i))
      self.horizontalLayout.addWidget(self.chk[i])
      self.chk[i].stateChanged.connect(self.chkStateChange)

    # Creation zone de texte
    self.lneMask = QtWidgets.QLineEdit(self.frame)
    self.lneMask.setMinimumSize(QSize(31, 19))
    self.lneMask.setMaximumSize(QSize(31, 19))
    self.lneMask.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
    self.lneMask.setObjectName("lneMask")
    self.lneMask.setText("0")
    validator = QIntValidator(0, 63, self)
    self.lneMask.setValidator(validator)
    self.horizontalLayout.addWidget(self.lneMask)
    self.lneMask.textChanged.connect(self.lneTextChanged)

    self.setLayout(self.horizontalLayout)


  @pyqtSlot(int)
  def chkStateChange(self, value):
    if not self.__changeEnCours:
      self.__changeEnCours = True
      newVal = 0
      for i in range(6):
        if self.chk[i].isChecked():
          newVal += 2**i
      self.lneMask.setText(format(newVal))
      self.valueChanged.emit(newVal)
      self.__changeEnCours = False


  @pyqtSlot(str)
  def lneTextChanged(self, txt: str):
    if not self.__changeEnCours:
      self.__changeEnCours = True
      try:
        newVal = int(txt)
      except ValueError as e:
        self.lneMask.setText("0")
        newVal = 0
      for i in range(6):
        if newVal & 2**i:
          self.chk[i].setCheckState(Qt.CheckState.Checked)
        else:
          self.chk[i].setCheckState(Qt.CheckState.Unchecked)
      self.valueChanged.emit(newVal)
      self.__changeEnCours = False


  @pyqtSlot()
  def getValue(self):
    ''' Renvoie la valeur du masque '''
    return int(self.lneMask.text())


  @pyqtSlot(int)
  def setValue(self, val: int):
    ''' affecte une nouvelle valeur au masque '''
    self.lneMask.setText(format(val))


  # Definie la propriete pour permettre la configuration par Designer
  value = pyqtProperty(int, fget=getValue, fset=setValue)


  @pyqtSlot()
  def getNbAxes(self):
    ''' Renvoie le nombre d'axes geres '''
    return self.__nbAxes


  @pyqtSlot(int)
  def setNbAxes(self, val: int):
    ''' Affecte le nombre d'axes gérés (valeur entre 3 et 6) '''
    if val < 3 or val > 6:
      raise RuntimeError(self.tr("The number of axis should be between 3 and 6!"))
    self.__nbAxes = val
    for i in range(6):
      if i < val:
        self.chk[i].setEnabled(True)
      else:
        self.chk[i].setEnabled(False)


  # Definie la propriete pour permettre la configuration par Designer
  nbAxes = pyqtProperty(int, fget=getNbAxes, fset=setNbAxes)









