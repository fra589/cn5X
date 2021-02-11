# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2021 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QValidator, QPalette
from cn5X_config import *
from grblCom import grblCom
from dlgG28_30_1 import *
from msgbox import *

class dlgG28_30_1(QObject):
  ''' Classe assurant la gestion de la boite de dialogue G92 '''

  def __init__(self, Gpos, grbl: grblCom, decoder, axisNumber: int, axisNames: list):
    super().__init__()
    self.__dlg = QDialog()
    self.di = Ui_dlgG28_30_1()
    self.di.setupUi(self.__dlg)

    self.__Gpos      = Gpos # Doit être G28 ou G30
    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames

    self.__settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)

    # G28 ou G30
    self.di.lblMessage.setText(self.tr("Save the current machine position (MPos) in the {}.1 Grbl's location?").format(self.__Gpos))
    
    # Affichage confirmation ou non...
    self.__dontConfirm = self.__settings.value("dontConfirm{}.1".format(self.__Gpos), False, type=bool)
    self.di.chkDontShow.setChecked(self.__dontConfirm)

    # Mise à jour de l'interface en fonction de la définition des axes:
    self.di.lblLblPosX.setText(self.tr("{}").format(self.__axisNames[0]))
    self.di.lblLblPosY.setText(self.tr("{}").format(self.__axisNames[1]))
    self.di.lblLblPosZ.setText(self.tr("{}").format(self.__axisNames[2]))
    if self.__nbAxis > 3:
      self.di.lblLblPosA.setText(self.tr("{}").format(self.__axisNames[3]))
      self.di.lblLblPosA.setEnabled(True)
      self.di.lblPosA.setEnabled(True)
    else:
      self.di.lblLblPosA.setText(self.tr("-"))
      self.di.lblLblPosA.setEnabled(False)
      self.di.lblPosA.setEnabled(False)
    if self.__nbAxis > 4:
      self.di.lblLblPosB.setText(self.tr("{}").format(self.__axisNames[4]))
      self.di.lblLblPosB.setEnabled(True)
      self.di.lblPosB.setEnabled(True)
    else:
      self.di.lblLblPosB.setText(self.tr("-"))
      self.di.lblLblPosB.setEnabled(False)
      self.di.lblPosB.setEnabled(False)
    if self.__nbAxis > 5:
      self.di.lblLblPosC.setText(self.tr("{}").format(self.__axisNames[5]))
      self.di.lblLblPosC.setEnabled(True)
      self.di.lblPosC.setEnabled(True)
    else:
      self.di.lblLblPosC.setText(self.tr("-"))
      self.di.lblLblPosC.setEnabled(False)
      self.di.lblPosC.setEnabled(False)
    
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
    
    # Connection des actions
    self.di.buttonBox.button(QDialogButtonBox.Yes).clicked.connect(self.on_btnYes)
    self.di.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.__dlg.close)


  def showDialog(self):
    
    if not self.__dontConfirm:
      # Centrage de la boite de dialogue sur la fenetre principale
      ParentX = self.parent().geometry().x()
      ParentY = self.parent().geometry().y()
      ParentWidth = self.parent().geometry().width()
      ParentHeight = self.parent().geometry().height()
      myWidth = self.__dlg.geometry().width()
      myHeight = self.__dlg.geometry().height()
      self.__dlg.setFixedSize(self.__dlg.geometry().width(),self.__dlg.geometry().height())
      self.__dlg.move(ParentX + ((ParentWidth - myWidth) / 2),ParentY + ((ParentHeight - myHeight) / 2),)
      self.__dlg.setWindowFlags(Qt.Window | Qt.Dialog)

      RC = self.__dlg.exec()
      return RC

    else:
      self.__grblCom.gcodePush("{}.1".format(self.__Gpos))
      return QDialog.Accepted


  def on_btnYes(self):
    ''' Envoi G28.1 ou G30.1 '''
    self.__grblCom.gcodePush("{}.1".format(self.__Gpos))
    # Enregistre l'état de chkDontShow
    self.__settings.setValue("dontConfirm{}.1".format(self.__Gpos), self.di.chkDontShow.isChecked())
    # Fermeture de la dialog
    self.__dlg.close()







