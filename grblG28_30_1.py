# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file is part of cn5X++                                             '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
' under the terms of the GNU General Public License as published by       '
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
'                                      cn5X_dlgG92                                   '
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

import os
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QSettings
from PyQt6.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QValidator, QPalette
from cn5X_config import *
from grblCom import grblCom
from msgbox import *

class dlgG28_30_1(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue G92 '''

  def __init__(self, Gpos, grbl: grblCom, decoder, axisNumber: int, axisNames: list):
    super().__init__()
    self.di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgG28_30_1.ui"), self)

    self.__Gpos      = Gpos # Doit être G28, G28.1, G30 ou G30.1
    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames

    self.__settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)
    

    # G28, G28.1, G30 ou G30.1
    if self.__Gpos[-2:] == ".1":
      self.setWindowTitle(self.tr("Define {} absolute position?").format(self.__Gpos))
      self.di.lblPosition.setText(self.tr("Current machine position (MPos)"))
      self.di.lblMessage.setText(self.tr("Save the current machine position (MPos) in the {} Grbl's location?").format(self.__Gpos))
      self.enableDisableCheckBoxes(False)
      # Affichage confirmation ou non...
      self.__dontConfirm = self.__settings.value("dontConfirm{}".format(self.__Gpos), False, type=bool)
      self.di.chkDontShow.setChecked(self.__dontConfirm)
      self.di.chkDontShow.setVisible(True)
    else:
      self.setWindowTitle(self.tr("Go to {} stored location?").format(self.__Gpos))
      self.di.lblPosition.setText(self.tr("Current {} defined position").format(self.__Gpos))
      text  = self.tr("Make a rapid move from current location to the position defined by the last {}?\n".format(self.__Gpos))
      text += self.tr("If no positions are stored with {} then all axes will go to the machine origin.".format(self.__Gpos))
      self.di.lblMessage.setText(text)
      self.enableDisableCheckBoxes(True)
      # Affichage confirmation ou non...
      self.__dontConfirm = False
      self.di.chkDontShow.setChecked(self.__dontConfirm)
      self.di.chkDontShow.setVisible(False)
    
    # Image G28, G28.1, G30 ou G30.1
    self.di.imageDeco.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "images/question{}.svg".format(self.__Gpos))))

    # Mise à jour de l'interface en fonction de la définition des axes:
    self.di.lblLblPosX.setText(self.tr("{}").format(self.__axisNames[0]))
    self.di.lblLblPosY.setText(self.tr("{}").format(self.__axisNames[1]))
    self.di.lblLblPosZ.setText(self.tr("{}").format(self.__axisNames[2]))
    if self.__nbAxis > 3:
      self.di.lblLblPosA.setText(self.tr("{}").format(self.__axisNames[3]))
      self.enableDisableAxis('A', True)
    else:
      self.di.lblLblPosA.setText(self.tr("-"))
      self.enableDisableAxis('A', False)
    if self.__nbAxis > 4:
      self.di.lblLblPosB.setText(self.tr("{}").format(self.__axisNames[4]))
      self.enableDisableAxis('B', True)
    else:
      self.di.lblLblPosB.setText(self.tr("-"))
      self.enableDisableAxis('B', False)
    if self.__nbAxis > 5:
      self.di.lblLblPosC.setText(self.tr("{}").format(self.__axisNames[5]))
      self.enableDisableAxis('C', True)
    else:
      self.di.lblLblPosC.setText(self.tr("-"))
      self.enableDisableAxis('C', False)
    
    if self.__Gpos[-2:] == ".1":
      # Mise à jour des valeurs avec les coordonnées courantes
      self.di.lblPosX.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[0])))
      self.di.lblPosY.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[1])))
      self.di.lblPosZ.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[2])))
      if self.__nbAxis > 3:
        self.di.lblPosA.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[3])))
      else:
        self.di.lblPosA.setText("-")
      if self.__nbAxis > 4:
        self.di.lblPosB.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[4])))
      else:
        self.di.lblPosB.setText("-")
      if self.__nbAxis > 5:
        self.di.lblPosC.setText("{:+0.3f}".format(self.__decode.getMpos(self.__axisNames[5])))
      else:
        self.di.lblPosC.setText("-")
    else:
      if self.__Gpos[:3] == "G28":
        # Mise à jour des valeurs avec les valeurs G28 courantes
        self.di.lblPosX.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[0])))
        self.di.lblPosY.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[1])))
        self.di.lblPosZ.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[2])))
        if self.__nbAxis > 3:
          self.di.lblPosA.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[3])))
        else:
          self.di.lblPosA.setText("-")
        if self.__nbAxis > 4:
          self.di.lblPosB.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[4])))
        else:
          self.di.lblPosB.setText("-")
        if self.__nbAxis > 5:
          self.di.lblPosC.setText("{:+0.3f}".format(self.__decode.getG28(self.__axisNames[5])))
        else:
          self.di.lblPosC.setText("-")
      else:
        # Mise à jour des valeurs avec les valeurs G30 courantes
        self.di.lblPosX.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[0])))
        self.di.lblPosY.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[1])))
        self.di.lblPosZ.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[2])))
        if self.__nbAxis > 3:
          self.di.lblPosA.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[3])))
        else:
          self.di.lblPosA.setText("-")
        if self.__nbAxis > 4:
          self.di.lblPosB.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[4])))
        else:
          self.di.lblPosB.setText("-")
        if self.__nbAxis > 5:
          self.di.lblPosC.setText("{:+0.3f}".format(self.__decode.getG30(self.__axisNames[5])))
        else:
          self.di.lblPosC.setText("-")

    # Connection des actions
    self.di.buttonBox.button(QDialogButtonBox.StandardButton.Yes).clicked.connect(self.on_btnYes)
    self.di.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
    self.di.chkPosX.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosX, 0))
    self.di.chkPosY.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosY, 1))
    self.di.chkPosZ.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosZ, 2))
    self.di.chkPosA.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosA, 3))
    self.di.chkPosB.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosB, 4))
    self.di.chkPosC.stateChanged.connect(lambda: self.on_chkPos_changed(self.di.chkPosC, 5))

  def showDialog(self):
    
    if not self.__dontConfirm:
      # Centrage de la boite de dialogue sur la fenetre principale
      ParentX = self.parent().geometry().x()
      ParentY = self.parent().geometry().y()
      ParentWidth = self.parent().geometry().width()
      ParentHeight = self.parent().geometry().height()
      myWidth = self.geometry().width()
      myHeight = self.geometry().height()
      self.setFixedSize(self.geometry().width(),self.geometry().height())
      self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
      self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.Dialog)

      RC = self.exec()
      return RC

    else:
      self.__grblCom.gcodePush("{}".format(self.__Gpos))
      return QDialog.Accepted


  def on_btnYes(self):
    ''' Envoi G28.1 ou G30.1 '''
    if self.__Gpos[-2:] == ".1":
      # Envoi direct G28.1 ou G30.1 car pas de sélection d'axes possibles
      self.__grblCom.gcodePush("{}".format(self.__Gpos))
    else:
      # Vérifie quels axes traiter pour G28 et G30
      gcodeOrder = self.__Gpos
      axesTraites = []
      gcodeAxisComplement = ""
      axeEnMoins = False
      i = 0
      for chk in [self.di.chkPosX, self.di.chkPosY, self.di.chkPosZ, self.di.chkPosA, self.di.chkPosB, self.di.chkPosC]:
        if chk.isChecked():
          a = self.__axisNames[i]
          if self.__Gpos[:3] == "G28":
            val = self.__decode.getG28(a) - self.__decode.getWco(a)
          else:
            val = self.__decode.getG30(a) - self.__decode.getWco(a)
          if a not in axesTraites:
            gcodeAxisComplement += "{}{}".format(a, val)
            axesTraites.append(a)
        else:
          if chk.isEnabled():
            axeEnMoins = True
        i += 1
      if axeEnMoins:
        gcodeOrder += gcodeAxisComplement
      self.__grblCom.gcodePush(gcodeOrder)

    # Enregistre l'état de chkDontShow
    self.__settings.setValue("dontConfirm{}".format(self.__Gpos), self.di.chkDontShow.isChecked())
    # Fermeture de la dialog
    self.close()


  def enableDisableCheckBoxes(self, enabling: bool):
    '''
    self.di.chkPosX.setEnabled(enabling)
    self.di.chkPosY.setEnabled(enabling)
    self.di.chkPosZ.setEnabled(enabling)
    self.di.chkPosA.setEnabled(enabling)
    self.di.chkPosB.setEnabled(enabling)
    self.di.chkPosC.setEnabled(enabling)
    '''
    for a in ['X', 'Y', 'Z', 'A', 'B', 'C']:
      self.enableDisableChkPos(a, enabling)


  def enableDisableAxis(self, axis: str, enabling: bool):

    activeColor   = self.di.lblLblPosX.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText).name()   # #000000
    disabledColor = self.di.lblLblPosX.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText).name() # #bebebe
    
    lblLblPos = self.di.frmMPos.findChild(QtWidgets.QLabel, "lblLblPos{}".format(axis))
    if lblLblPos is not None:
      lblLblPos.setEnabled(enabling)
      if enabling:
        lblLblPos.setStyleSheet("color: {};".format(activeColor))
      else:
        lblLblPos.setStyleSheet("color: {};".format(disabledColor))

    lblPos = self.di.frmMPos.findChild(QtWidgets.QLabel, "lblPos{}".format(axis))
    if lblPos is not None:
      lblPos.setEnabled(enabling)
      if enabling:
        lblPos.setStyleSheet("color: {};".format(activeColor))
      else:
        lblPos.setStyleSheet("color: {};".format(disabledColor))

    self.enableDisableChkPos(axis, enabling)

  def enableDisableChkPos(self, axis: str, enabling: bool):

    enabledStyle   = "QCheckBox{margin-left: 6px;}"
    enabledStyle  += "QCheckBox::indicator{width: 24px;	height: 24px;}"
    enabledStyle  += "QCheckBox::indicator:unchecked {image: url(" + os.path.join(os.path.dirname(__file__), "images/chkBoxUnChecked.svg") + ");}"
    enabledStyle  += "QCheckBox::indicator:checked {image: url(" + os.path.join(os.path.dirname(__file__), "images/chkBoxChecked.svg") + ");}"
    disabledStyle  = "QCheckBox{margin-left: 6px;}"
    disabledStyle += "QCheckBox::indicator{width: 24px;	height: 24px;}"
    disabledStyle += "QCheckBox::indicator:unchecked {image: url(" + os.path.join(os.path.dirname(__file__), "images/chkBoxDisabledUnChecked.svg") + ");}"
    disabledStyle += "QCheckBox::indicator:checked {image: url(" + os.path.join(os.path.dirname(__file__), "images/chkBoxDisabledChecked.svg") + ");}"
    
    toolTipEnabled  = self.tr("Uncheck to keep this axis at its current position")
    toolTipDisabled = ""
    
    chkPos = self.di.frmMPos.findChild(QtWidgets.QCheckBox, "chkPos{}".format(axis))
    if chkPos is not None:
      if self.__Gpos[-2:] == ".1":
        chkPos.setEnabled(False)
        chkPos.setChecked(False)
        chkPos.setStyleSheet(disabledStyle)
        chkPos.setToolTip(toolTipDisabled)
      else:
        if enabling:
          chkPos.setEnabled(True)
          chkPos.setStyleSheet(enabledStyle)
          chkPos.setToolTip(toolTipEnabled)
        else:
          chkPos.setEnabled(False)
          chkPos.setChecked(False)
          chkPos.setStyleSheet(disabledStyle)
          chkPos.setToolTip(toolTipDisabled)


  def on_chkPos_changed(self, chkChanged, axisNumChanged):
    ''' Vérifie si 2 axes ont le même nom, et dans ce cas, assure que les 2 axes soit cochée ou décochés de la même manière '''
    i = 0
    for chk in [self.di.chkPosX, self.di.chkPosY, self.di.chkPosZ, self.di.chkPosA, self.di.chkPosB, self.di.chkPosC]:
      if chk != chkChanged:
        if i >= self.__nbAxis:
          break
        if self.__axisNames[i] == self.__axisNames[axisNumChanged]:
          # Force le même état des 2 checkBox 
          chk.setChecked(chkChanged.isChecked())
      i += 1







