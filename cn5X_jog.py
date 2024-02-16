# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_probe.py, is part of cn5X++                             '
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

import os
from PyQt6 import QtCore, uic
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QSettings, QEvent
from PyQt6.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt6.QtGui import QPalette
from cn5X_config import *
from grblCom import grblCom
from cnQPushButton import cnQPushButton


class dlgJog(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue Jogging '''

  sig_close = pyqtSignal()         # Emis a la fermeture de la boite de dialogue

  def __init__(self, grbl: grblCom, decoder, axisNumber: int, axisNames: list):
    super().__init__()
    self.di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgJog.ui"), self)

    self.finished.connect(self.sig_close.emit)
    
    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames
    
    # Mémorise les couleurs standard des spin boxes
    self.activeColor   = self.di.dsbJogX.palette().color(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText).name()
    self.disabledColor = self.di.dsbJogX.palette().color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText).name()

    # Mise à jour de l'interface en fonction de la définition des axes:
    self.di.chkJogX.setText(self.tr("Jog {} axis".format(self.__axisNames[0])))
    self.di.btnJogX.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[0])))
    self.di.chkJogY.setText(self.tr("Jog {} axis".format(self.__axisNames[1])))
    self.di.btnJogY.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[1])))
    self.di.chkJogZ.setText(self.tr("Jog {} axis".format(self.__axisNames[2])))
    self.di.btnJogZ.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[2])))
    if self.__nbAxis > 3:
      self.di.chkJogA.setText(self.tr("Jog {} axis".format(self.__axisNames[3])))
      self.di.btnJogA.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[3])))
      self.di.chkJogA.setEnabled(True)
      self.di.dsbJogA.setEnabled(True)
    else:
      self.di.chkJogA.setText(self.tr("Jog - axis"))
      self.di.btnJogA.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJogNone.svg"))
      self.di.chkJogA.setEnabled(False)
      self.di.dsbJogA.setEnabled(False)
    if self.__nbAxis > 4:
      self.di.chkJogB.setText(self.tr("Jog {} axis".format(self.__axisNames[4])))
      self.di.btnJogB.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[4])))
      self.di.chkJogB.setEnabled(True)
      self.di.dsbJogB.setEnabled(True)
    else:
      self.di.chkJogB.setText(self.tr("Jog - axis"))
      self.di.btnJogB.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJogNone.svg"))
      self.di.chkJogB.setEnabled(False)
      self.di.dsbJogB.setEnabled(False)
    if self.__nbAxis > 5:
      self.di.chkJogC.setText(self.tr("Jog {} axis".format(self.__axisNames[5])))
      self.di.btnJogC.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[5])))
      self.di.chkJogC.setEnabled(True)
      self.di.dsbJogC.setEnabled(True)
    else:
      self.di.chkJogC.setText(self.tr("Jog - axis"))
      self.di.btnJogC.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJogNone.svg"))
      self.di.chkJogC.setEnabled(False)
      self.di.dsbJogC.setEnabled(False)

    # Mise à jour des valeurs des spinBoxs avec les coordonnées courantes
    self.setCurrentValues()
    
    # Connection des actions

    self.di.btnJog.clicked.connect(lambda: self.on_btnJog())
    self.di.btnJogX.clicked.connect(lambda: self.on_btnJog(0, self.di.dsbJogX))
    self.di.btnJogY.clicked.connect(lambda: self.on_btnJog(1, self.di.dsbJogY))
    self.di.btnJogZ.clicked.connect(lambda: self.on_btnJog(2, self.di.dsbJogZ))
    self.di.btnJogA.clicked.connect(lambda: self.on_btnJog(3, self.di.dsbJogA))
    self.di.btnJogB.clicked.connect(lambda: self.on_btnJog(4, self.di.dsbJogB))
    self.di.btnJogC.clicked.connect(lambda: self.on_btnJog(5, self.di.dsbJogC))
    
    self.di.btnJogStop.clicked.connect(self.jogCancel)
    self.di.buttonBox.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close)

    self.di.rbtMPos.toggled.connect(self.on_rbtMPos)
    self.di.rbtG90.toggled.connect(self.on_rbtG90)

    self.di.chkJogX.toggled.connect(lambda: self.on_chkJog_toogle('X'))
    self.di.chkJogY.toggled.connect(lambda: self.on_chkJog_toogle('Y'))
    self.di.chkJogZ.toggled.connect(lambda: self.on_chkJog_toogle('Z'))
    self.di.chkJogA.toggled.connect(lambda: self.on_chkJog_toogle('A'))
    self.di.chkJogB.toggled.connect(lambda: self.on_chkJog_toogle('B'))
    self.di.chkJogC.toggled.connect(lambda: self.on_chkJog_toogle('C'))

    self.di.chkJogX.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogX, 0))
    self.di.chkJogY.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogY, 1))
    self.di.chkJogZ.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogZ, 2))
    self.di.chkJogA.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogA, 3))
    self.di.chkJogB.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogB, 4))
    self.di.chkJogC.stateChanged.connect(lambda: self.on_chkJog_changed(self.di.chkJogC, 5))

    self.di.dsbJogX.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogX, self.di.chkJogX, 0))
    self.di.dsbJogY.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogY, self.di.chkJogY, 1))
    self.di.dsbJogZ.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogZ, self.di.chkJogZ, 2))
    self.di.dsbJogA.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogA, self.di.chkJogA, 3))
    self.di.dsbJogB.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogB, self.di.chkJogB, 4))
    self.di.dsbJogC.valueChanged.connect(lambda: self.on_dsbJog_changed(self.di.dsbJogC, self.di.chkJogC, 5))

    self.installEventFilter(self)


  def showDialog(self):
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.geometry().width()
    myHeight = self.geometry().height()
    self.setFixedSize(self.geometry().width(),self.geometry().height())
    self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Tool)
    
    # Mise à jour de la vitesse de déplacement:
    self.di.dsbJogSpeed.setValue(self.parent().ui.dsbJogSpeed.value())

    # Use exec in place of self.open() to make the dialog application modal.
    RC = self.exec()
    return RC


  def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.KeyPress:
      if event.key() == Qt.Key.Key_Escape:
        self.jogCancel()
        return True
    return super(QDialog, self).eventFilter(obj, event)


  def setInitialCheckState(self):
    # Force l'état unchecked des boxes
    self.di.chkJogX.setChecked(False)
    self.di.chkJogY.setChecked(False)
    self.di.chkJogZ.setChecked(False)
    self.di.chkJogA.setChecked(False)
    self.di.chkJogB.setChecked(False)
    self.di.chkJogC.setChecked(False)


  def setCurrentValues(self):
    ''' Mise à jour des valeurs des spinBoxs avec les coordonnées courantes '''
    if self.di.rbtMPos.isChecked():
      self.di.dsbJogX.setValue(self.__decode.getMpos(self.__axisNames[0]))
      self.di.dsbJogY.setValue(self.__decode.getMpos(self.__axisNames[1]))
      self.di.dsbJogZ.setValue(self.__decode.getMpos(self.__axisNames[2]))
      if self.__nbAxis > 3:
        self.di.dsbJogA.setValue(self.__decode.getMpos(self.__axisNames[3]))
      if self.__nbAxis > 4:
        self.di.dsbJogB.setValue(self.__decode.getMpos(self.__axisNames[4]))
      if self.__nbAxis > 5:
        self.di.dsbJogC.setValue(self.__decode.getMpos(self.__axisNames[5]))
    else: # self.di.rbtWPos.isChecked() = True
      if self.di.rbtG90.isChecked():
        self.di.dsbJogX.setValue(self.__decode.getWpos(self.__axisNames[0]))
        self.di.dsbJogY.setValue(self.__decode.getWpos(self.__axisNames[1]))
        self.di.dsbJogZ.setValue(self.__decode.getWpos(self.__axisNames[2]))
        if self.__nbAxis > 3:
          self.di.dsbJogA.setValue(self.__decode.getWpos(self.__axisNames[3]))
        if self.__nbAxis > 4:
          self.di.dsbJogB.setValue(self.__decode.getWpos(self.__axisNames[4]))
        if self.__nbAxis > 5:
          self.di.dsbJogC.setValue(self.__decode.getWpos(self.__axisNames[5]))
      else:
        self.di.dsbJogX.setValue(0.0)
        self.di.dsbJogY.setValue(0.0)
        self.di.dsbJogZ.setValue(0.0)
        if self.__nbAxis > 3:
          self.di.dsbJogA.setValue(0.0)
        if self.__nbAxis > 4:
          self.di.dsbJogB.setValue(0.0)
        if self.__nbAxis > 5:
          self.di.dsbJogC.setValue(0.0)
    # Force le décochage des checkboxs
    self.setInitialCheckState()


  def on_btnJog(self, axisNum: int = None, spinBox: QDoubleSpinBox = None):

    gcode = "$J="
    if self.di.rbtMPos.isChecked():
      gcode += "G53"
    elif self.di.rbtG90.isChecked():
      gcode += "G90"
    else: # self.di.rbtG91.isChecked() = True
      gcode += "G91"
    if axisNum is not None:
      # Jog d'un seul axe
      gcode += "{}{:0.3f}".format(self.__axisNames[axisNum], spinBox.value())
    else:
      # Jog de tous les axes cochés
      axesTraites = []
      i = 0
      for chk, val in [(self.di.chkJogX, self.di.dsbJogX.value()), 
                       (self.di.chkJogY, self.di.dsbJogY.value()), 
                       (self.di.chkJogZ, self.di.dsbJogZ.value()), 
                       (self.di.chkJogA, self.di.dsbJogA.value()), 
                       (self.di.chkJogB, self.di.dsbJogB.value()), 
                       (self.di.chkJogC, self.di.dsbJogC.value())]:
        if chk.isChecked():
          a = self.__axisNames[i]
          if a not in axesTraites:
            gcode += "{}{:0.3f}".format(a, val)
            axesTraites.append(a)
        i += 1
    # On ajoute la vitesse de déplacement
    gcode += "F{:0.2f}".format(self.di.dsbJogSpeed.value())
    
    # On envoi le mouvement
    self.__grblCom.gcodePush(gcode)


  def jogCancel(self):
    self.__grblCom.clearCom()
    self.__grblCom.realTimePush(REAL_TIME_JOG_CANCEL) # Commande realtime Jog Cancel


  def on_rbtMPos(self):
    self.di.frmG90G91.setEnabled(not self.di.rbtMPos.isChecked())
    self.setCurrentValues()


  def on_rbtG90(self):
    self.setCurrentValues()


  def on_chkJog_toogle(self, axis: str):
    ''' Change la couleur des spinBoxes dynamiquement et traite l'activation ou la désactivation du bouton d'envoi '''
    if axis == 'X':
      self.di.btnJogX.setEnabled(self.di.chkJogX.isChecked())
      self.di.btnJogX.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[0])))
      if self.di.chkJogX.isChecked():
        self.di.dsbJogX.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogX.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'Y':
      self.di.btnJogY.setEnabled(self.di.chkJogY.isChecked())
      self.di.btnJogY.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[1])))
      if self.di.chkJogY.isChecked():
        self.di.dsbJogY.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogY.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'Z':
      self.di.btnJogZ.setEnabled(self.di.chkJogZ.isChecked())
      self.di.btnJogZ.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[2])))
      if self.di.chkJogZ.isChecked():
        self.di.dsbJogZ.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogZ.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'A':
      self.di.btnJogA.setEnabled(self.di.chkJogA.isChecked())
      self.di.btnJogA.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[3])))
      if self.di.chkJogA.isChecked():
        self.di.dsbJogA.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogA.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'B':
      self.di.btnJogB.setEnabled(self.di.chkJogB.isChecked())
      self.di.btnJogB.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[4])))
      if self.di.chkJogB.isChecked():
        self.di.dsbJogB.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogB.setStyleSheet("color: {};".format(self.disabledColor))
    if axis == 'C':
      self.di.btnJogC.setEnabled(self.di.chkJogC.isChecked())
      self.di.btnJogC.changeIcon(os.path.join(os.path.dirname(__file__), "images/btnJog{}.svg".format(self.__axisNames[5])))
      if self.di.chkJogC.isChecked():
        self.di.dsbJogC.setStyleSheet("color: {};".format(self.activeColor))
      else:
        self.di.dsbJogC.setStyleSheet("color: {};".format(self.disabledColor))
      
    if self.di.chkJogX.isChecked() \
    or self.di.chkJogY.isChecked() \
    or self.di.chkJogZ.isChecked() \
    or self.di.chkJogA.isChecked() \
    or self.di.chkJogB.isChecked() \
    or self.di.chkJogC.isChecked():
      self.di.btnJog.setEnabled(True)
    else:
      self.di.btnJog.setEnabled(False)


  def on_chkJog_changed(self, chkChanged, axisNumChanged):
    ''' Vérifie si 2 axes ont le même nom, et dans ce cas, assure que les 2 axes soit cochée ou décochés de la même manière '''
    i = 0
    for chk in [self.di.chkJogX, self.di.chkJogY, self.di.chkJogZ, self.di.chkJogA, self.di.chkJogB, self.di.chkJogC]:
      if chk != chkChanged:
        if i >= self.__nbAxis:
          break
        if self.__axisNames[i] == self.__axisNames[axisNumChanged]:
          # Force le même état des 2 checkBox 
          chk.setChecked(chkChanged.isChecked())
      i += 1


  def on_dsbJog_changed(self, dbsChanged, chkJog, axisNumChanged):
    # Coche la case correspondante
    chkJog.setChecked(True)
    # Vérifie si 2 axes ont le même nom, et dans ce cas, assure que les 2 valeurs soient la même
    i = 0
    for dbs in [self.di.dsbJogX, self.di.dsbJogY, self.di.dsbJogZ, self.di.dsbJogA, self.di.dsbJogB, self.di.dsbJogC]:
      if dbs != dbsChanged:
        if i >= self.__nbAxis:
          break
        if self.__axisNames[i] == self.__axisNames[axisNumChanged]:
          # Force le même état des 2 checkBox 
          dbs.setValue(dbsChanged.value())
      i += 1







    
