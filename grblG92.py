# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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
from dlgG92 import *
from msgbox import *

class dlgG92(QObject):
  ''' Classe assurant la gestion de la boite de dialogue G92 '''

  def __init__(self, grbl: grblCom, decoder, axisNumber: int, axisNames: list):
    super().__init__()
    self.__dlgG92 = QDialog()
    self.di = Ui_dlgG92()
    self.di.setupUi(self.__dlgG92)

    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames

    self.__settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)
    self.di.chkAutoclose.setChecked(self.__settings.value("G92/autoCloseDialog", False, type=bool))

    # Mémorise les couleurs standard des spin boxes
    self.activeColor   = self.di.dsbG92valeurX.palette().color(QPalette.Active, QPalette.WindowText).name()
    self.disabledColor = self.di.dsbG92valeurX.palette().color(QPalette.Disabled, QPalette.WindowText).name()
    
    # Mise à jour de l'interface en fonction de la définition des axes:
    self.di.chkDefineX.setText("Assign {} value".format(self.__axisNames[0]))
    self.di.chkDefineY.setText("Assign {} value".format(self.__axisNames[1]))
    self.di.chkDefineZ.setText("Assign {} value".format(self.__axisNames[2]))
    if self.__nbAxis > 3:
      self.di.chkDefineA.setText("Assign {} value".format(self.__axisNames[3]))
      self.di.chkDefineA.setEnabled(True)
      self.di.dsbG92valeurA.setEnabled(True)
    else:
      self.di.chkDefineA.setText("Assign - value")
      self.di.chkDefineA.setEnabled(False)
      self.di.dsbG92valeurA.setEnabled(False)
    if self.__nbAxis > 4:
      self.di.chkDefineB.setText("Assign {} value".format(self.__axisNames[4]))
      self.di.chkDefineB.setEnabled(True)
      self.di.dsbG92valeurB.setEnabled(True)
    else:
      self.di.chkDefineB.setText("Assign - value")
      self.di.chkDefineB.setEnabled(False)
      self.di.dsbG92valeurB.setEnabled(False)
    if self.__nbAxis > 5:
      self.di.chkDefineC.setText("Assign {} value".format(self.__axisNames[5]))
      self.di.chkDefineC.setEnabled(True)
      self.di.dsbG92valeurC.setEnabled(True)
    else:
      self.di.chkDefineC.setText("Assign - value")
      self.di.chkDefineC.setEnabled(False)
      self.di.dsbG92valeurC.setEnabled(False)

    palette = self.di.dsbG92valeurX.palette()
    palette.setColor(QPalette.Inactive, QPalette.WindowText, Qt.GlobalColor.red)
    self.di.dsbG92valeurX.setPalette(palette)
    
    # Mise à jour des valeurs avec les coordonnées courantes
    self.di.dsbG92valeurX.setValue(self.__decode.getWpos(self.__axisNames[0]))
    self.di.dsbG92valeurY.setValue(self.__decode.getWpos(self.__axisNames[1]))
    self.di.dsbG92valeurZ.setValue(self.__decode.getWpos(self.__axisNames[2]))
    if self.__nbAxis > 3:
      self.di.dsbG92valeurA.setValue(self.__decode.getWpos(self.__axisNames[3]))
    if self.__nbAxis > 4:
      self.di.dsbG92valeurB.setValue(self.__decode.getWpos(self.__axisNames[4]))
    if self.__nbAxis > 5:
      self.di.dsbG92valeurC.setValue(self.__decode.getWpos(self.__axisNames[5]))
    
    # Connection des actions
    self.di.chkAutoclose.toggled.connect(self.on_chkAutoclose_toggled)
    self.di.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.__dlgG92.close)
    self.di.btnSetOriginG92.clicked.connect(self.on_btnSetOriginG92)
    self.di.btnSetOriginG92_1.clicked.connect(self.on_btnSetOriginG92_1)

    self.di.chkDefineX.toggled.connect(lambda: self.on_chkDefine_toogle('X'))
    self.di.chkDefineY.toggled.connect(lambda: self.on_chkDefine_toogle('Y'))
    self.di.chkDefineZ.toggled.connect(lambda: self.on_chkDefine_toogle('Z'))
    self.di.chkDefineA.toggled.connect(lambda: self.on_chkDefine_toogle('A'))
    self.di.chkDefineB.toggled.connect(lambda: self.on_chkDefine_toogle('B'))
    self.di.chkDefineC.toggled.connect(lambda: self.on_chkDefine_toogle('C'))

    self.di.chkDefineX.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineX, 0))
    self.di.chkDefineY.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineY, 1))
    self.di.chkDefineZ.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineZ, 2))
    self.di.chkDefineA.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineA, 3))
    self.di.chkDefineB.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineB, 4))
    self.di.chkDefineC.stateChanged.connect(lambda: self.on_chkDefine_changed(self.di.chkDefineC, 5))

    self.di.dsbG92valeurX.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurX, self.di.chkDefineX, 0))
    self.di.dsbG92valeurY.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurY, self.di.chkDefineY, 1))
    self.di.dsbG92valeurZ.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurZ, self.di.chkDefineZ, 2))
    self.di.dsbG92valeurA.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurA, self.di.chkDefineA, 3))
    self.di.dsbG92valeurB.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurB, self.di.chkDefineB, 4))
    self.di.dsbG92valeurC.valueChanged.connect(lambda: self.on_dsbG92valeur_changed(self.di.dsbG92valeurC, self.di.chkDefineC, 5))
    

  def on_dsbG92valeur_changed(self, dbsChanged, chkDefine, axisNumChanged):
    # Coche la case correspondante
    chkDefine.setChecked(True)
    # Vérifie si 2 axes ont le même nom, et dans ce cas, assure que les 2 valeurs soient la même
    i = 0
    for dbs in [self.di.dsbG92valeurX, self.di.dsbG92valeurY, self.di.dsbG92valeurZ, self.di.dsbG92valeurA, self.di.dsbG92valeurB, self.di.dsbG92valeurC]:
      if dbs != dbsChanged:
        if i >= self.__nbAxis:
          break
        if self.__axisNames[i] == self.__axisNames[axisNumChanged]:
          # Force le même état des 2 checkBox 
          dbs.setValue(dbsChanged.value())
      i += 1


  def on_chkDefine_changed(self, chkChanged, axisNumChanged):
    ''' Vérifie si 2 axes ont le même nom, et dans ce cas, assure que les 2 axes soit cochée ou décochés de la même manière '''
    i = 0
    for chk in [self.di.chkDefineX, self.di.chkDefineY, self.di.chkDefineZ, self.di.chkDefineA, self.di.chkDefineB, self.di.chkDefineC]:
      if chk != chkChanged:
        if i >= self.__nbAxis:
          break
        if self.__axisNames[i] == self.__axisNames[axisNumChanged]:
          # Force le même état des 2 checkBox 
          chk.setChecked(chkChanged.isChecked())
      i += 1


  def showDialog(self):
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.__dlgG92.geometry().width()
    myHeight = self.__dlgG92.geometry().height()
    self.__dlgG92.setFixedSize(self.__dlgG92.geometry().width(),self.__dlgG92.geometry().height())
    self.__dlgG92.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.__dlgG92.setWindowFlags(Qt.Window | Qt.Dialog)

    RC = self.__dlgG92.exec()
    return RC


  def on_chkAutoclose_toggled(self):
    self.__settings.setValue("G92/autoCloseDialog", self.di.chkAutoclose.isChecked())


  def on_btnSetOriginG92(self):
    '''
    Construit et envoi l'ordre G92 à Grbl
    '''
    originGcode = "G92"
    if self.di.chkDefineX.isChecked(): originGcode += "X{}".format(float(self.di.dsbG92valeurX.value()))
    if self.di.chkDefineY.isChecked(): originGcode += "Y{}".format(float(self.di.dsbG92valeurY.value()))
    if self.di.chkDefineZ.isChecked(): originGcode += "Z{}".format(float(self.di.dsbG92valeurZ.value()))
    if self.di.chkDefineA.isChecked(): originGcode += "A{}".format(float(self.di.dsbG92valeurA.value()))
    if self.di.chkDefineB.isChecked(): originGcode += "B{}".format(float(self.di.dsbG92valeurB.value()))
    if self.di.chkDefineC.isChecked(): originGcode += "C{}".format(float(self.di.dsbG92valeurC.value()))

    # Envoi du changement d'origine à Grbl
    self.__grblCom.gcodePush(originGcode)
    if self.di.chkAutoclose.isChecked():
      # Fermeture de la dialog
      self.__dlgG92.close()


  def on_btnSetOriginG92_1(self):
    ''' Envoi G92.1 '''
    self.__grblCom.gcodePush("G92.1")
    if self.di.chkAutoclose.isChecked():
      # Fermeture de la dialog
      self.__dlgG92.close()


  def on_chkDefine_toogle(self, axis: str):
    ''' Change la couleur des spinBoxes dynamiquement et traite l'activation ou la désactivation du bouton d'envoi '''
    if axis == 'X':
      if self.di.chkDefineX.isChecked():
        self.di.dsbG92valeurX.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurX.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'Y':
      if self.di.chkDefineY.isChecked():
        self.di.dsbG92valeurY.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurY.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'Z':
      if self.di.chkDefineZ.isChecked():
        self.di.dsbG92valeurZ.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurZ.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'A':
      if self.di.chkDefineA.isChecked():
        self.di.dsbG92valeurA.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurA.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'B':
      if self.di.chkDefineB.isChecked():
        self.di.dsbG92valeurB.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurB.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'C':
      if self.di.chkDefineC.isChecked():
        self.di.dsbG92valeurC.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbG92valeurC.setStyleSheet("color: {};".format(self.disabledColor))
    
    if self.di.chkDefineX.isChecked() \
    or self.di.chkDefineY.isChecked() \
    or self.di.chkDefineZ.isChecked() \
    or self.di.chkDefineA.isChecked() \
    or self.di.chkDefineB.isChecked() \
    or self.di.chkDefineC.isChecked():
      self.di.btnSetOriginG92.setEnabled(True)
    else:
      self.di.btnSetOriginG92.setEnabled(False)





