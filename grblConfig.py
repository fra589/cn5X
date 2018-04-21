# -*- coding: UTF-8 -*-

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

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QValidator
from cn5X_config import *
from grblCom import grblCom
from dlgConfig import *
from msgbox import *
from compilOptions import grblCompilOptions

class upperCaseValidator(QValidator):
  def validate(self, string, pos):
    return QValidator.Acceptable, string.upper(), pos
    # for old code still using QString, use this instead
    # string.replace(0, string.count(), string.toUpper())
    # return QtGui.QValidator.Acceptable, pos

class grblConfig(QObject):
  ''' Classe assurant la gestion de la boite de dialogue de configuration de Grbl '''

  # Liste des contrôles éditables (49 contrôles)
  #---------------------------------------------------------
  # lneEEPROM lneN0 lneN1
  # spinStepPulse spinStepIdleDelay emStepPortInvert emDirectionPortInvert chkStepEnableInvert chkLimitPinsInvert chkProbePinInvert
  # lneStatusReport dsbJunctionDeviation dsbArcTolerance chkReportInches
  # chkSoftLimits chkHardLimits chkHomingCycle emHomeDirInvert dsbHomingFeed dsbHomingSeek spinHomingDebounce dsbHomingPullOff
  # spinMaxSpindle spinMinSpindle chkLaserMode
  # dsbStepsX dsbStepsY dsbStepsZ dsbStepsA dsbStepsB dsbStepsC dsbTravelX dsbTravelY dsbTravelZ dsbTravelA dsbTravelB dsbTravelC
  # dsbMaxRateX dsbMaxRateY dsbMaxRateZ dsbMaxRateA dsbMaxRateB dsbMaxRateC dsbAccelX dsbAccelY dsbAccelZ dsbAccelA dsbAccelB dsbAccelC


  def __init__(self, grbl: grblCom):
    super().__init__()
    self.__dlgConfig = QDialog()
    self.__di = Ui_dlgConfig()
    self.__di.setupUi(self.__dlgConfig)
    self.__configChanged = False
    self.__changedParams = []
    self.ucase = upperCaseValidator(self)

    # Barre de boutons de la boite de dialogue
    self.__buttonApply   = self.__di.buttonBox.addButton(QDialogButtonBox.Apply)
    self.__buttonApply.setToolTip("Applique les modifications et ferme la boîte de dialogue.")
    self.__buttonApply.setEnabled(False)
    self.__buttonDiscard = self.__di.buttonBox.addButton(QDialogButtonBox.Discard)
    self.__buttonDiscard.setToolTip("Ferme la boîte de dialogue sans valider les modifications.")
    self.__buttonReset   = self.__di.buttonBox.addButton(QDialogButtonBox.Reset)
    self.__buttonReset.setEnabled(False)
    self.__buttonReset.setToolTip("Recharge tous les paramètres à partir de leur valeur actuelle dans Grbl.")
    self.__buttonFactory = self.__di.buttonBox.addButton("Reset factory", QDialogButtonBox.ActionRole)
    self.__buttonFactory.setToolTip("Réinitialise tous les paramètres à partir de leurs valeurs d'origine\ndéfinis lors de la compilation de Grbl.")

    self.__buttonApply.pressed.connect(self.on_Apply)
    self.__buttonDiscard.pressed.connect(self.on_Discard)
    self.__buttonReset.pressed.connect(self.on_Reset)
    self.__buttonFactory.pressed.connect(self.on_ResetFactory)

    # Connexion des changements d'états des QWidgets des paramètres de Grbl
    # QCheckBox
    self.__di.chkStepEnableInvert.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkStepEnableInvert))
    self.__di.chkLimitPinsInvert.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkLimitPinsInvert))
    self.__di.chkProbePinInvert.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkProbePinInvert))
    self.__di.chkReportInches.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkReportInches))
    self.__di.chkSoftLimits.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkSoftLimits))
    self.__di.chkHardLimits.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkHardLimits))
    self.__di.chkHomingCycle.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkHomingCycle))
    self.__di.chkLaserMode.stateChanged.connect(lambda: self.chkStateChange(self.__di.chkLaserMode))
    # QSpinBox, QDoubleSpinBox
    self.__di.spinStepPulse.valueChanged.connect(lambda: self.spinChange(self.__di.spinStepPulse))
    self.__di.spinStepIdleDelay.valueChanged.connect(lambda: self.spinChange(self.__di.spinStepIdleDelay))
    self.__di.spinHomingDebounce.valueChanged.connect(lambda: self.spinChange(self.__di.spinHomingDebounce))
    self.__di.spinMaxSpindle.valueChanged.connect(lambda: self.spinChange(self.__di.spinMaxSpindle))
    self.__di.spinMinSpindle.valueChanged.connect(lambda: self.spinChange(self.__di.spinMinSpindle))
    self.__di.dsbJunctionDeviation.valueChanged.connect(lambda: self.spinChange(self.__di.dsbJunctionDeviation))
    self.__di.dsbArcTolerance.valueChanged.connect(lambda: self.spinChange(self.__di.dsbArcTolerance))
    self.__di.dsbHomingFeed.valueChanged.connect(lambda: self.spinChange(self.__di.dsbHomingFeed))
    self.__di.dsbHomingSeek.valueChanged.connect(lambda: self.spinChange(self.__di.dsbHomingSeek))
    self.__di.dsbHomingPullOff.valueChanged.connect(lambda: self.spinChange(self.__di.dsbHomingPullOff))
    self.__di.dsbStepsX.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsX))
    self.__di.dsbStepsY.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsY))
    self.__di.dsbStepsZ.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsZ))
    self.__di.dsbStepsA.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsA))
    self.__di.dsbStepsB.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsB))
    self.__di.dsbStepsC.valueChanged.connect(lambda: self.spinChange(self.__di.dsbStepsC))
    self.__di.dsbTravelX.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelX))
    self.__di.dsbTravelY.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelY))
    self.__di.dsbTravelZ.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelZ))
    self.__di.dsbTravelA.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelA))
    self.__di.dsbTravelB.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelB))
    self.__di.dsbTravelC.valueChanged.connect(lambda: self.spinChange(self.__di.dsbTravelC))
    self.__di.dsbMaxRateX.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateX))
    self.__di.dsbMaxRateY.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateY))
    self.__di.dsbMaxRateZ.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateZ))
    self.__di.dsbMaxRateA.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateA))
    self.__di.dsbMaxRateB.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateB))
    self.__di.dsbMaxRateC.valueChanged.connect(lambda: self.spinChange(self.__di.dsbMaxRateC))
    self.__di.dsbAccelX.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelX))
    self.__di.dsbAccelY.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelY))
    self.__di.dsbAccelZ.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelZ))
    self.__di.dsbAccelA.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelA))
    self.__di.dsbAccelB.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelB))
    self.__di.dsbAccelC.valueChanged.connect(lambda: self.spinChange(self.__di.dsbAccelC))
    # qwEditMask
    self.__di.emStepPortInvert.valueChanged.connect(lambda: self.editMaskChange(self.__di.emStepPortInvert))
    self.__di.emDirectionPortInvert.valueChanged.connect(lambda: self.editMaskChange(self.__di.emDirectionPortInvert))
    self.__di.emHomeDirInvert.valueChanged.connect(lambda: self.editMaskChange(self.__di.emHomeDirInvert))
    # QLineEdit
    self.__di.lneEEPROM.textChanged.connect(lambda: self.textChange(self.__di.lneEEPROM))
    self.__di.lneN0.textChanged.connect(lambda: self.textChange(self.__di.lneN0))
    self.__di.lneN1.textChanged.connect(lambda: self.textChange(self.__di.lneN1))
    self.__di.lneEEPROM.setValidator(self.ucase)
    self.__di.lneN0.setValidator(self.ucase)
    self.__di.lneN1.setValidator(self.ucase)
    self.__di.lneStatusReport.textChanged.connect(lambda: self.textChange(self.__di.lneStatusReport))

    self.__grblCom = grbl
    self.__grblCom.sig_init.connect(self.on_sig_init)
    self.__grblCom.sig_config.connect(self.on_sig_config)


  def showDialog(self):
    self.__getGrblParams()
    reply = self.__dlgConfig.exec_()
    print("Reponse de la boite de dialogue = {}".format(reply))


  def __getGrblParams(self):
    self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET, COM_FLAG_NO_OK)     # Envoi Ctrl+X.
    self.__grblCom.gcodePush(CMD_GRBL_GET_BUILD_INFO, COM_FLAG_NO_OK)     # $I
    self.__grblCom.gcodePush(CMD_GRBL_GET_STARTUP_BLOCKS, COM_FLAG_NO_OK) # $N
    self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS, COM_FLAG_NO_OK)       # $$


  def on_sig_init(self, data: str):
    #print("on_sig_init({})".format(data))
    decodeInit = data.split(" ")
    self.__di.lblGrblName.setText(decodeInit[0])
    self.__di.lblGrblVersion.setText(decodeInit[1])


  def on_sig_config(self, data: str):
    #print("on_sig_config({})".format(data))
    if   data[:1] == "$":
      print(data)
      # Onglet matériel
      if data[:3] == '$0=':
        self.__di.spinStepPulse.setValue(int(data.split("=")[1]))
      elif data[:3] == '$1=':
        self.__di.spinStepIdleDelay.setValue(int(data.split("=")[1]))
      elif data[:3] == '$2=':
        self.__di.emStepPortInvert.setValue(int(data.split("=")[1]))
      elif data[:3] == '$3=':
        self.__di.emDirectionPortInvert.setValue(int(data.split("=")[1]))
      elif data[:3] == '$4=':
        if data.split("=")[1] == '0':
          self.__di.chkStepEnableInvert.setCheckState(Qt.Unchecked)
          self.__di.chkStepEnableInvert.setText("False")
        else:
          self.__di.chkStepEnableInvert.setCheckState(Qt.Checked)
          self.__di.chkStepEnableInvert.setText("True")
      elif data[:3] == '$5=':
        if data.split("=")[1] == '0':
          self.__di.chkLimitPinsInvert.setCheckState(Qt.Unchecked)
          self.__di.chkLimitPinsInvert.setText("False")
        else:
          self.__di.chkLimitPinsInvert.setCheckState(Qt.Checked)
          self.__di.chkLimitPinsInvert.setText("True")
      elif data[:3] == '$6=':
        if data.split("=")[1] == '0':
          self.__di.chkProbePinInvert.setCheckState(Qt.Unchecked)
          self.__di.chkProbePinInvert.setText("False")
        else:
          self.__di.chkProbePinInvert.setCheckState(Qt.Checked)
          self.__di.chkProbePinInvert.setText("True")
      # Onglet Unités
      elif data[:4] == '$10=':
        self.__di.lneStatusReport.setText(data.split("=")[1])
      elif data[:4] == '$11=':
        self.__di.dsbJunctionDeviation.setValue(float(data.split("=")[1]))
      elif data[:4] == '$12=':
        self.__di.dsbArcTolerance.setValue(float(data.split("=")[1]))
      elif data[:4] == '$13=':
        if data.split("=")[1] == '0':
          self.__di.chkReportInches.setCheckState(Qt.Unchecked)
          self.__di.chkReportInches.setText("False")
        else:
          self.__di.chkReportInches.setCheckState(Qt.Checked)
          self.__di.chkReportInches.setText("True")
      # Onglet Limites
      elif data[:4] == '$20=':
        if data.split("=")[1] == '0':
          self.__di.chkSoftLimits.setCheckState(Qt.Unchecked)
          self.__di.chkSoftLimits.setText("False")
        else:
          self.__di.chkSoftLimits.setCheckState(Qt.Checked)
          self.__di.chkSoftLimits.setText("True")
      elif data[:4] == '$21=':
        if data.split("=")[1] == '0':
          self.__di.chkHardLimits.setCheckState(Qt.Unchecked)
          self.__di.chkHardLimits.setText("False")
        else:
          self.__di.chkHardLimits.setCheckState(Qt.Checked)
          self.__di.chkHardLimits.setText("True")
      elif data[:4] == '$22=':
        if data.split("=")[1] == '0':
          self.__di.chkHomingCycle.setCheckState(Qt.Unchecked)
          self.__di.chkHomingCycle.setText("False")
        else:
          self.__di.chkHomingCycle.setCheckState(Qt.Checked)
          self.__di.chkHomingCycle.setText("True")
      elif data[:4] == '$23=':
        self.__di.emHomeDirInvert.setValue(int(data.split("=")[1]))
      elif data[:4] == '$24=':
        self.__di.dsbHomingFeed.setValue(float(data.split("=")[1]))
      elif data[:4] == '$25=':
        self.__di.dsbHomingSeek.setValue(float(data.split("=")[1]))
      elif data[:4] == '$26=':
        self.__di.spinHomingDebounce.setValue(int(data.split("=")[1]))
      elif data[:4] == '$27=':
        self.__di.dsbHomingPullOff.setValue(float(data.split("=")[1]))
      # Onglet Broche
      elif data[:4] == '$30=':
        self.__di.spinMaxSpindle.setValue(int(data.split("=")[1]))
      elif data[:4] == '$31=':
        self.__di.spinMinSpindle.setValue(int(data.split("=")[1]))
      elif data[:4] == '$32=':
        if data.split("=")[1] == '0':
          self.__di.chkLaserMode.setCheckState(Qt.Unchecked)
          self.__di.chkLaserMode.setText("False")
        else:
          self.__di.chkLaserMode.setCheckState(Qt.Checked)
          self.__di.chkLaserMode.setText("True")
      # Onglet Courses
      elif data[:5] == '$100=':
        self.__di.dsbStepsX.setValue(float(data.split("=")[1]))
      elif data[:5] == '$101=':
        self.__di.dsbStepsY.setValue(float(data.split("=")[1]))
      elif data[:5] == '$102=':
        self.__di.dsbStepsZ.setValue(float(data.split("=")[1]))
      elif data[:5] == '$103=':
        self.__di.dsbStepsA.setValue(float(data.split("=")[1]))
      elif data[:5] == '$104=':
        self.__di.dsbStepsB.setValue(float(data.split("=")[1]))
      elif data[:5] == '$105=':
        self.__di.dsbStepsC.setValue(float(data.split("=")[1]))
      elif data[:5] == '$130=':
        self.__di.dsbTravelX.setValue(float(data.split("=")[1]))
      elif data[:5] == '$131=':
        self.__di.dsbTravelY.setValue(float(data.split("=")[1]))
      elif data[:5] == '$132=':
        self.__di.dsbTravelZ.setValue(float(data.split("=")[1]))
      elif data[:5] == '$133=':
        self.__di.dsbTravelA.setValue(float(data.split("=")[1]))
      elif data[:5] == '$134=':
        self.__di.dsbTravelB.setValue(float(data.split("=")[1]))
      elif data[:5] == '$135=':
        self.__di.dsbTravelC.setValue(float(data.split("=")[1]))
      # Onglet Vitesses
      elif data[:5] == '$110=':
        self.__di.dsbMaxRateX.setValue(float(data.split("=")[1]))
      elif data[:5] == '$111=':
        self.__di.dsbMaxRateY.setValue(float(data.split("=")[1]))
      elif data[:5] == '$112=':
        self.__di.dsbMaxRateZ.setValue(float(data.split("=")[1]))
      elif data[:5] == '$113=':
        self.__di.dsbMaxRateA.setValue(float(data.split("=")[1]))
      elif data[:5] == '$114=':
        self.__di.dsbMaxRateB.setValue(float(data.split("=")[1]))
      elif data[:5] == '$115=':
        self.__di.dsbMaxRateC.setValue(float(data.split("=")[1]))
      elif data[:5] == '$120=':
        self.__di.dsbAccelX.setValue(float(data.split("=")[1]))
      elif data[:5] == '$121=':
        self.__di.dsbAccelY.setValue(float(data.split("=")[1]))
      elif data[:5] == '$122=':
        self.__di.dsbAccelZ.setValue(float(data.split("=")[1]))
      elif data[:5] == '$123=':
        self.__di.dsbAccelA.setValue(float(data.split("=")[1]))
      elif data[:5] == '$124=':
        self.__di.dsbAccelB.setValue(float(data.split("=")[1]))
      elif data[:5] == '$125=':
        self.__di.dsbAccelC.setValue(float(data.split("=")[1]))
      # Onglet Initialisation
      elif data[:3] == "$N0":
        self.__di.lneN0.setText(data.split("=")[1])
      elif data[:3] == "$N1":
        self.__di.lneN1.setText(data.split("=")[1])
    elif data[:5] == "[VER:":
      print(data)
      decodeVer=data.split(":")[1].split(".")
      self.__di.lblGrblDate.setText(decodeVer[2])
      self.__di.lneEEPROM.setText(data[1:-1].split(":")[2])
    elif data[:5] == "[AXS:":
      self.__di.lblGrblNbAxes.setText(data[:-1].split(":")[1])
    elif data[:5] == "[OPT:": # BLOCK_BUFFER_SIZE,RX_BUFFER_SIZE
      self.__di.lblGrblOptions.setText(data[:-1].split(":")[1])
      decodeOpt = data[:-1].split(":")[1].split(',')
      self.__di.lblGrblBlockBufferSize.setText(decodeOpt[1])
      self.__di.lblGrblRxBufferSize.setText(decodeOpt[2])
      # remplir lstOptions avec la liste des options Grbl compilées
      model = QStandardItemModel(self.__di.lstOptions)
      for o in list(decodeOpt[0]):
        if grblCompilOptions[o][0]:
          item = QStandardItem("{} : {}".format(o, grblCompilOptions[o][0]))
          model.appendRow(item)
      self.__di.lstOptions.setModel(model)
    self.__configChanged     = False
    self.__buttonApply.setEnabled(False)
    self.__buttonReset.setEnabled(False)
    self.__changedParams.clear()


  @pyqtSlot()
  def on_Apply(self):
    print(self.__changedParams)
    # Applique les éléments modifiés
    # Onglet 1 Initialisation
    if self.__di.lneEEPROM.objectName() in self.__changedParams:
      print("$I={}".format(str(self.__di.lneEEPROM.text())))
      self.__grblCom.gcodePush("$I={}\0".format(str(self.__di.lneEEPROM.text())))
    if self.__di.lneN0.objectName() in self.__changedParams:
      print("$N0={}".format(str(self.__di.lneN0.text())))
      self.__grblCom.gcodePush("$N0={}\0".format(str(self.__di.lneN0.text())))
    if self.__di.lneN1.objectName() in self.__changedParams:
      print("$N1={}".format(str(self.__di.lneN1.text())))
      self.__grblCom.gcodePush("$N1={}\0".format(str(self.__di.lneN1.text())))
    # Onglet 2 Matériel
    if self.__di.spinStepPulse.objectName() in self.__changedParams: self.__grblCom.gcodePush("$0={}".format(self.__di.spinStepPulse.value()))
    if self.__di.spinStepIdleDelay.objectName() in self.__changedParams: self.__grblCom.gcodePush("$1={}".format(self.__di.spinStepIdleDelay.value()))
    if self.__di.emStepPortInvert.objectName() in self.__changedParams: self.__grblCom.gcodePush("$2={}".format(self.__di.emStepPortInvert.value()))
    if self.__di.emDirectionPortInvert.objectName() in self.__changedParams: self.__grblCom.gcodePush("$3=".format(self.__di.emDirectionPortInvert.value()))
    if self.__di.chkStepEnableInvert.objectName() in self.__changedParams:
      if self.__di.chkStepEnableInvert.isChecked():
        self.__grblCom.gcodePush("$4=1")
      else:
        self.__grblCom.gcodePush("$4=0")
    if self.__di.chkLimitPinsInvert.objectName() in self.__changedParams:
      if self.__di.chkLimitPinsInvert.isChecked():
        self.__grblCom.gcodePush("$5=1")
      else:
        self.__grblCom.gcodePush("$5=0")
    if self.__di.chkProbePinInvert.objectName() in self.__changedParams:
      if self.__di.chkProbePinInvert.isChecked():
        self.__grblCom.gcodePush("$6=1")
      else:
        self.__grblCom.gcodePush("$6=0")
    # Onglet 3 Unités
    if self.__di.lneStatusReport in self.__changedParams: self.__grblCom.gcodePush("$10={}".format(self.__di.lneStatusReport.text()))
    if self.__di.dsbJunctionDeviation.objectName() in self.__changedParams: self.__grblCom.gcodePush("$11={}".format(self.__di.dsbJunctionDeviation.value()))
    if self.__di.dsbArcTolerance.objectName() in self.__changedParams: self.__grblCom.gcodePush("$12={}".format(self.__di.dsbArcTolerance.value()))
    if self.__di.chkReportInches.objectName() in self.__changedParams:
      if self.__di.chkReportInches.isChecked():
        self.__grblCom.gcodePush("$13=1")
      else:
        self.__grblCom.gcodePush("$13=0")
    # Onglet 4 Limites
    if self.__di.chkSoftLimits.objectName() in self.__changedParams:
      if self.__di.chkSoftLimits.isChecked():
        self.__grblCom.gcodePush("$20=1")
      else:
        self.__grblCom.gcodePush("$20=0")
    if self.__di.chkHardLimits.objectName() in self.__changedParams:
      if self.__di.chkHardLimits.isChecked():
        self.__grblCom.gcodePush("$21")
      else:
        self.__grblCom.gcodePush("$21=0")
    if self.__di.chkHomingCycle.objectName() in self.__changedParams:
      if self.__di.chkHomingCycle.isChecked():
        self.__grblCom.gcodePush("$22=1")
      else:
        self.__grblCom.gcodePush("$22=0")
    if self.__di.emHomeDirInvert.objectName() in self.__changedParams: self.__grblCom.gcodePush("$23=".format(self.__di.emHomeDirInvert.value()))
    if self.__di.dsbHomingFeed.objectName() in self.__changedParams: self.__grblCom.gcodePush("$24={}".format(self.__di.dsbHomingFeed.value()))
    if self.__di.dsbHomingSeek.objectName() in self.__changedParams: self.__grblCom.gcodePush("$25={}".format(self.__di.dsbHomingSeek.value()))
    if self.__di.spinHomingDebounce.objectName() in self.__changedParams: self.__grblCom.gcodePush("$26={}".format(self.__di.spinHomingDebounce.value()))
    if self.__di.dsbHomingPullOff.objectName() in self.__changedParams: self.__grblCom.gcodePush("$27={}".format(self.__di.dsbHomingPullOff.value()))
    # Onglet 5 Broche
    if self.__di.spinMaxSpindle.objectName() in self.__changedParams: self.__grblCom.gcodePush("$30={}".format(self.__di.spinMaxSpindle.value()))
    if self.__di.spinMinSpindle.objectName() in self.__changedParams: self.__grblCom.gcodePush("$31={}".format(self.__di.spinMinSpindle.value()))
    if self.__di.chkLaserMode.objectName() in self.__changedParams:
      if self.__di.chkHomingCycle.isChecked():
        self.__grblCom.gcodePush("$32=1")
      else:
        self.__grblCom.gcodePush("$32=0")
    # Onglet 6 Courses
    if self.__di.dsbStepsX.objectName() in self.__changedParams: self.__grblCom.gcodePush("$100={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbStepsY.objectName() in self.__changedParams: self.__grblCom.gcodePush("$101={}".format(self.__di.dsbStepsY.value()))
    if self.__di.dsbStepsZ.objectName() in self.__changedParams: self.__grblCom.gcodePush("$102={}".format(self.__di.dsbStepsZ.value()))
    if self.__di.dsbStepsA.objectName() in self.__changedParams: self.__grblCom.gcodePush("$103={}".format(self.__di.dsbStepsA.value()))
    if self.__di.dsbStepsB.objectName() in self.__changedParams: self.__grblCom.gcodePush("$104={}".format(self.__di.dsbStepsB.value()))
    if self.__di.dsbStepsC.objectName() in self.__changedParams: self.__grblCom.gcodePush("$105={}".format(self.__di.dsbStepsC.value()))
    if self.__di.dsbTravelX.objectName() in self.__changedParams: self.__grblCom.gcodePush("$130={}".format(self.__di.dsbTravelX.value()))
    if self.__di.dsbTravelY.objectName() in self.__changedParams: self.__grblCom.gcodePush("$131={}".format(self.__di.dsbTravelY.value()))
    if self.__di.dsbTravelZ.objectName() in self.__changedParams: self.__grblCom.gcodePush("$132={}".format(self.__di.dsbTravelZ.value()))
    if self.__di.dsbTravelA.objectName() in self.__changedParams: self.__grblCom.gcodePush("$133={}".format(self.__di.dsbTravelA.value()))
    if self.__di.dsbTravelB.objectName() in self.__changedParams: self.__grblCom.gcodePush("$134={}".format(self.__di.dsbTravelB.value()))
    if self.__di.dsbTravelC.objectName() in self.__changedParams: self.__grblCom.gcodePush("$135={}".format(self.__di.dsbTravelC.value()))
    # Onglet 7 Vitesses
    if self.__di.dsbMaxRateX.objectName() in self.__changedParams: self.__grblCom.gcodePush("$110={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbMaxRateY.objectName() in self.__changedParams: self.__grblCom.gcodePush("$111={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbMaxRateZ.objectName() in self.__changedParams: self.__grblCom.gcodePush("$112={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbMaxRateA.objectName() in self.__changedParams: self.__grblCom.gcodePush("$113={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbMaxRateB.objectName() in self.__changedParams: self.__grblCom.gcodePush("$114={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbMaxRateC.objectName() in self.__changedParams: self.__grblCom.gcodePush("$115={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelX.objectName() in self.__changedParams: self.__grblCom.gcodePush("$120={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelY.objectName() in self.__changedParams: self.__grblCom.gcodePush("$121={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelZ.objectName() in self.__changedParams: self.__grblCom.gcodePush("$122={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelA.objectName() in self.__changedParams: self.__grblCom.gcodePush("$123={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelB.objectName() in self.__changedParams: self.__grblCom.gcodePush("$124={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbAccelC.objectName() in self.__changedParams: self.__grblCom.gcodePush("$125={}".format(self.__di.dsbStepsX.value()))
    self.__dlgConfig.done(QDialog.Accepted)


  @pyqtSlot()
  def on_Discard(self):
    self.__dlgConfig.reject()


  @pyqtSlot()
  def on_Reset(self):
    self.__getGrblParams()


  @pyqtSlot()
  def on_ResetFactory(self):
    m = msgBox(
        title     = "Restorer la configuration usine",
        text      = "Etes vous sûrs ? Restorer la configuration usine restore tous les paramètres tels qu'ils étaient lors de la génération du microcode Grbl.",
        info      = "Toutes les modifications et réglages effectués sur cette instance de Grbl seront définitevement perdus !",
        icon      = msgIconList.Question,
        stdButton = msgButtonList.Yes | msgButtonList.Cancel,
        defButton = msgButtonList.Cancel,
        escButton = msgButtonList.Cancel
    )
    if m.afficheMsg() == msgButtonList.Yes:
      self.__grblCom.gcodePush(CMD_GRBL_RESET_ALL_EEPROM)       # $RST=*
      self.__getGrblParams()
    self.__configChanged     = False
    self.__buttonApply.setEnabled(False)
    self.__buttonReset.setEnabled(False)
    self.__changedParams.clear()


  @pyqtSlot(QCheckBox)
  def chkStateChange(self, chk: QCheckBox):
    if chk.checkState() == Qt.Checked:
      chk.setText("True")
    else:
      chk.setText("False")
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # mémorise que le paramètre à changé
    if not chk.objectName() in self.__changedParams:
      self.__changedParams.append(chk.objectName())

  @pyqtSlot(QSpinBox)
  @pyqtSlot(QDoubleSpinBox)
  def spinChange(self, spin):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # mémorise que le paramètre à changé
    if not spin.objectName() in self.__changedParams:
      self.__changedParams.append(spin.objectName())


  @pyqtSlot(qwEditMask)
  def editMaskChange(self, em):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # mémorise que le paramètre à changé
    if not em.objectName() in self.__changedParams:
      self.__changedParams.append(em.objectName())


  @pyqtSlot(QLineEdit)
  def textChange(self, lne: QLineEdit):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # mémorise que le paramètre à changé
    if not lne.objectName() in self.__changedParams:
      self.__changedParams.append(lne.objectName())






