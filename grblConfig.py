# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2023 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

import os
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QValidator
from cn5X_config import *
from grblCom import grblCom
from msgbox import *
from compilOptions import grblCompilOptions
from qweditmask import qwEditMask


class upperCaseValidator(QValidator):
  def validate(self, string, pos):
    return QValidator.State.Acceptable, string.upper(), pos


class grblConfig(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue de configuration de Grbl '''

  # Liste des controles editables (49 controles)
  #---------------------------------------------------------
  # lneEEPROM lneN0 lneN1
  # spinStepPulse spinStepIdleDelay emStepPortInvert emDirectionPortInvert chkStepEnableInvert chkLimitPinsInvert chkProbePinInvert
  # lneStatusReport dsbJunctionDeviation dsbArcTolerance chkReportInches
  # chkSoftLimits chkHardLimits chkHomingCycle emHomeDirInvert dsbHomingFeed dsbHomingSeek spinHomingDebounce dsbHomingPullOff
  # spinMaxSpindle spinMinSpindle chkLaserMode
  # dsbStepsX dsbStepsY dsbStepsZ dsbStepsA dsbStepsB dsbStepsC dsbTravelX dsbTravelY dsbTravelZ dsbTravelA dsbTravelB dsbTravelC
  # dsbMaxRateX dsbMaxRateY dsbMaxRateZ dsbMaxRateA dsbMaxRateB dsbMaxRateC dsbAccelX dsbAccelY dsbAccelZ dsbAccelA dsbAccelB dsbAccelC

  sig_config_changed = pyqtSignal(str)
  sig_log            = pyqtSignal(int, str) # Pour renvoyer les erreurs dans la log cn5X++

  def __init__(self, grbl: grblCom, nbAxis: int, axisNames: list):
    super().__init__()
    self.__di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgConfig.ui"), self)
    
    self.__configChanged = False
    self.__changedParams = []
    self.__nbAxis = nbAxis
    self.__axisNames = axisNames
    self.__setNbAxes(self.__nbAxis, self.__axisNames)

    self.ucase = upperCaseValidator(self)

    # Barre de boutons de la boite de dialogue
    self.__buttonApply   = self.__di.buttonBox.addButton(QDialogButtonBox.StandardButton.Apply)
    self.__buttonApply.setToolTip(self.tr("Apply the changes."))
    self.__buttonApply.setEnabled(False)
    self.__buttonDiscard = self.__di.buttonBox.addButton(QDialogButtonBox.StandardButton.Close)
    self.__buttonDiscard.setToolTip(self.tr("Close the dialog box without validating modifications."))
    self.__buttonReset   = self.__di.buttonBox.addButton(QDialogButtonBox.StandardButton.Reset)
    self.__buttonReset.setEnabled(False)
    self.__buttonReset.setToolTip(self.tr("Reloads all parameters from their current values in Grbl."))
    self.__buttonFactory = self.__di.buttonBox.addButton("Reset factory", QDialogButtonBox.ButtonRole.ActionRole)
    self.__buttonFactory.setToolTip(self.tr("Reset all parameters to their original values\ndefined when compiling Grbl."))

    self.__buttonApply.pressed.connect(self.on_Apply)
    self.__buttonDiscard.pressed.connect(self.on_Discard)
    self.__buttonReset.pressed.connect(self.on_Reset)
    self.__buttonFactory.pressed.connect(self.on_ResetFactory)

    # Connexion des changements d'etats des QWidgets des parametres de Grbl
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
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.geometry().width()
    myHeight = self.geometry().height()
    self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.setFixedSize(self.geometry().width(),self.geometry().height())
    self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.Dialog)
    self.__getGrblParams()
    RC = self.exec()
    return RC


  def __getGrblParams(self):
    self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET, COM_FLAG_NO_OK)     # Envoi Ctrl+X.
    self.__grblCom.gcodePush(CMD_GRBL_GET_BUILD_INFO, COM_FLAG_NO_OK)     # $I
    self.__grblCom.gcodePush(CMD_GRBL_GET_STARTUP_BLOCKS, COM_FLAG_NO_OK) # $N
    self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS, COM_FLAG_NO_OK)       # $$


  def on_sig_init(self, data: str):
    decodeInit = data.split(" ")
    self.__di.lblGrblName.setText(decodeInit[0])
    self.__di.lblGrblVersion.setText(decodeInit[1])


  def on_sig_config(self, data: str):
    if   data[:1] == "$":
      # Onglet materiel
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
          self.__di.chkStepEnableInvert.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkStepEnableInvert.setText("False")
        else:
          self.__di.chkStepEnableInvert.setCheckState(Qt.CheckState.Checked)
          self.__di.chkStepEnableInvert.setText("True")
      elif data[:3] == '$5=':
        if data.split("=")[1] == '0':
          self.__di.chkLimitPinsInvert.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkLimitPinsInvert.setText("False")
        else:
          self.__di.chkLimitPinsInvert.setCheckState(Qt.CheckState.Checked)
          self.__di.chkLimitPinsInvert.setText("True")
      elif data[:3] == '$6=':
        if data.split("=")[1] == '0':
          self.__di.chkProbePinInvert.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkProbePinInvert.setText("False")
        else:
          self.__di.chkProbePinInvert.setCheckState(Qt.CheckState.Checked)
          self.__di.chkProbePinInvert.setText("True")
      # Onglet Unites
      elif data[:4] == '$10=':
        self.__di.lneStatusReport.setText(data.split("=")[1])
      elif data[:4] == '$11=':
        self.__di.dsbJunctionDeviation.setValue(float(data.split("=")[1]))
      elif data[:4] == '$12=':
        self.__di.dsbArcTolerance.setValue(float(data.split("=")[1]))
      elif data[:4] == '$13=':
        if data.split("=")[1] == '0':
          self.__di.chkReportInches.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkReportInches.setText("False")
        else:
          self.__di.chkReportInches.setCheckState(Qt.CheckState.Checked)
          self.__di.chkReportInches.setText("True")
      # Onglet Limites
      elif data[:4] == '$20=':
        if data.split("=")[1] == '0':
          self.__di.chkSoftLimits.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkSoftLimits.setText("False")
        else:
          self.__di.chkSoftLimits.setCheckState(Qt.CheckState.Checked)
          self.__di.chkSoftLimits.setText("True")
      elif data[:4] == '$21=':
        if data.split("=")[1] == '0':
          self.__di.chkHardLimits.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkHardLimits.setText("False")
        else:
          self.__di.chkHardLimits.setCheckState(Qt.CheckState.Checked)
          self.__di.chkHardLimits.setText("True")
      elif data[:4] == '$22=':
        if data.split("=")[1] == '0':
          self.__di.chkHomingCycle.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkHomingCycle.setText("False")
        else:
          self.__di.chkHomingCycle.setCheckState(Qt.CheckState.Checked)
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
          self.__di.chkLaserMode.setCheckState(Qt.CheckState.Unchecked)
          self.__di.chkLaserMode.setText("False")
        else:
          self.__di.chkLaserMode.setCheckState(Qt.CheckState.Checked)
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
      try:
        decodeVer=data.split(":")[1].split(".")
        if len(decodeVer) == 3: # standard grbl(Mega-5X version is <major>.<minor>.<buildDate>
          self.__di.lblGrblDate.setText(decodeVer[2])
        else:
          # No build date ? not 5X standard, but trying to use it anyway...
          self.__di.lblGrblDate.setText("<unknow>")
        self.__di.lneEEPROM.setText(data[1:-1].split(":")[2])
      except IndexError as e:
        self.sig_log.emit(logSeverity.error.value, self.tr("grblConfig.on_sig_config(): IndexError: list index out of range in Grbl's version string <{}>").format(data))
    elif data[:5] == "[AXS:":
      self.__di.lblGrblNbAxes.setText(data[:-1].split(":")[1])
      self.__di.lblAxisName.setText(data[:-1].split(":")[2])
      self.__setNbAxes(int(data[:-1].split(":")[1]), data[:-1].split(":")[2])
    elif data[:5] == "[OPT:": # BLOCK_BUFFER_SIZE,RX_BUFFER_SIZE
      self.__di.lblGrblOptions.setText(data[:-1].split(":")[1])
      decodeOpt = data[:-1].split(":")[1].split(',')
      self.__di.lblGrblBlockBufferSize.setText(decodeOpt[1])
      self.__di.lblGrblRxBufferSize.setText(decodeOpt[2])
      # remplir lstOptions avec la liste des options Grbl compilees
      model = QStandardItemModel(self.__di.lstOptions)
      for o in list(decodeOpt[0]):
        try:
          if grblCompilOptions[o][0]:
            item = QStandardItem("{} : {}".format(o, grblCompilOptions[o][0]))
            model.appendRow(item)
        except KeyError:
          item = QStandardItem("{} : {}".format(o, "Unknown Grbl compil option"))
          model.appendRow(item)
            
      self.__di.lstOptions.setModel(model)
    self.__configChanged     = False
    self.__buttonApply.setEnabled(False)
    self.__buttonReset.setEnabled(False)
    self.__changedParams.clear()


  def __setNbAxes(self, nb: int, names: str):
    '''
    Active ou desactive les controles en fonction du nombre d'axes a gerer
    renomme les labels des axes en fonction de leur noms
    '''
    self.__di.emStepPortInvert.setNbAxes(nb)
    self.__di.emDirectionPortInvert.setNbAxes(nb)
    self.__di.emHomeDirInvert.setNbAxes(nb)
    # Controles d'edition de masques
    self.__di.lblMaskX.setText(names[0])
    self.__di.lblMaskX_2.setText(names[0])

    self.__di.lblMaskY.setText(names[1])
    self.__di.lblMaskY_2.setText(names[1])

    self.__di.lblMaskZ.setText(names[2])
    self.__di.lblMaskZ_2.setText(names[2])

    if nb > 3:
      self.__di.lblMaskA.setText(names[3])
      self.__di.lblMaskA_2.setText(names[3])
    else:
      self.__di.lblMaskA.setText("")
      self.__di.lblMaskA_2.setText("")

    if nb > 4:
      self.__di.lblMaskB.setText(names[4])
      self.__di.lblMaskB_2.setText(names[4])
    else:
      self.__di.lblMaskB.setText("")
      self.__di.lblMaskB_2.setText("")

    if nb > 5:
      self.__di.lblMaskC.setText(names[5])
      self.__di.lblMaskC_2.setText(names[5])
    else:
      self.__di.lblMaskC.setText("")
      self.__di.lblMaskC_2.setText("")

    # Parametres des axes
    self.__di.lblStepsX.setText(self.tr("{} steps/mm ($100)").format(names[0]))
    self.__di.lblRateX.setText(self.tr("{} Max rate, mm/min ($110)").format(names[0]))
    self.__di.lblAccelX.setText(self.tr("{} Acceleration, mm/sec^2 ($120)").format(names[0]))
    self.__di.lblTravelX.setText(self.tr("{} Max travel, mm ($130)").format(names[0]))

    self.__di.lblStepsY.setText(self.tr("{} steps/mm ($101)").format(names[1]))
    self.__di.lblRateY.setText(self.tr("{} Max rate, mm/min ($111)").format(names[1]))
    self.__di.lblAccelY.setText(self.tr("{} Acceleration, mm/sec^2 ($121)").format(names[1]))
    self.__di.lblTravelY.setText(self.tr("{} Max travel, mm ($131)").format(names[1]))

    self.__di.lblStepsZ.setText(self.tr("{} steps/mm ($102)").format(names[2]))
    self.__di.lblRateZ.setText(self.tr("{} Max rate, mm/min ($112)").format(names[2]))
    self.__di.lblAccelZ.setText(self.tr("{} Acceleration, mm/sec^2 ($122)").format(names[2]))
    self.__di.lblTravelZ.setText(self.tr("{} Max travel, mm ($132)").format(names[2]))

    if nb > 3:
      self.__di.lblStepsA.setText(self.tr("{} steps/mm ($103)").format(names[3]))
      self.__di.lblRateA.setText(self.tr("{} Max rate, mm/min ($113)").format(names[3]))
      self.__di.lblAccelA.setText(self.tr("{} Acceleration, mm/sec^2 ($123)").format(names[3]))
      self.__di.lblTravelA.setText(self.tr("{} Max travel, mm ($133)").format(names[3]))
    else:
      self.__di.lblStepsA.setText(self.tr("- steps/mm ($103)"))
      self.__di.lblRateA.setText(self.tr("- Max rate, mm/min ($113)"))
      self.__di.lblAccelA.setText(self.tr("- Acceleration, mm/sec^2 ($123)"))
      self.__di.lblTravelA.setText(self.tr("- Max travel, mm ($133)"))
      self.__di.lblStepsA.setEnabled(False)
      self.__di.lblRateA.setEnabled(False)
      self.__di.lblAccelA.setEnabled(False)
      self.__di.lblTravelA.setEnabled(False)
      self.__di.dsbStepsA.setEnabled(False)
      self.__di.dsbMaxRateA.setEnabled(False)
      self.__di.dsbAccelA.setEnabled(False)
      self.__di.dsbTravelA.setEnabled(False)

    if nb > 4:
      self.__di.lblStepsB.setText(self.tr("{} steps/mm ($104)").format(names[4]))
      self.__di.lblRateB.setText(self.tr("{} Max rate, mm/min ($114)").format(names[4]))
      self.__di.lblAccelB.setText(self.tr("{} Acceleration, mm/sec^2 ($124)").format(names[4]))
      self.__di.lblTravelB.setText(self.tr("{} Max travel, mm ($134)").format(names[4]))
    else:
      self.__di.lblStepsB.setText(self.tr("- steps/mm ($104)"))
      self.__di.lblRateB.setText(self.tr("- Max rate, mm/min ($114)"))
      self.__di.lblAccelB.setText(self.tr("- Acceleration, mm/sec^2 ($124)"))
      self.__di.lblTravelB.setText(self.tr("- Max travel, mm ($134)"))
      self.__di.lblStepsB.setEnabled(False)
      self.__di.lblRateB.setEnabled(False)
      self.__di.lblAccelB.setEnabled(False)
      self.__di.lblTravelB.setEnabled(False)
      self.__di.dsbStepsB.setEnabled(False)
      self.__di.dsbMaxRateB.setEnabled(False)
      self.__di.dsbAccelB.setEnabled(False)
      self.__di.dsbTravelB.setEnabled(False)

    if nb > 5:
      self.__di.lblStepsC.setText(self.tr("{} steps/mm ($105)").format(names[5]))
      self.__di.lblRateC.setText(self.tr("{} Max rate, mm/min ($115)").format(names[5]))
      self.__di.lblAccelC.setText(self.tr("{} Acceleration, mm/sec^2 ($125)").format(names[5]))
      self.__di.lblTravelC.setText(self.tr("{} Max travel, mm ($135)").format(names[5]))
    else:
      self.__di.lblStepsC.setText(self.tr("- steps/mm ($105)"))
      self.__di.lblRateC.setText(self.tr("- Max rate, mm/min ($115)"))
      self.__di.lblAccelC.setText(self.tr("- Acceleration, mm/sec^2 ($125)"))
      self.__di.lblTravelC.setText(self.tr("- Max travel, mm ($135)"))
      self.__di.lblStepsC.setEnabled(False)
      self.__di.lblRateC.setEnabled(False)
      self.__di.lblAccelC.setEnabled(False)
      self.__di.lblTravelC.setEnabled(False)
      self.__di.dsbStepsC.setEnabled(False)
      self.__di.dsbMaxRateC.setEnabled(False)
      self.__di.dsbAccelC.setEnabled(False)
      self.__di.dsbTravelC.setEnabled(False)


  @pyqtSlot()
  def on_Apply(self):
    """ Applique les elements modifies """
    self.sig_config_changed.emit(self.tr("Save modified parameters : {}").format(self.__changedParams))

    # Onglet 1 Initialisation
    if self.__di.lneEEPROM.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$I={}".format(str(self.__di.lneEEPROM.text())))
      self.__grblCom.gcodePush("$I={}\0".format(str(self.__di.lneEEPROM.text())))
    if self.__di.lneN0.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$N0={}".format(str(self.__di.lneN0.text())))
      self.__grblCom.gcodePush("$N0={}\0".format(str(self.__di.lneN0.text())))
    if self.__di.lneN1.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$N1={}".format(str(self.__di.lneN1.text())))
      self.__grblCom.gcodePush("$N1={}\0".format(str(self.__di.lneN1.text())))

    # Onglet 2 Materiel
    if self.__di.spinStepPulse.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$0={}".format(self.__di.spinStepPulse.value()))
      self.__grblCom.gcodePush("$0={}".format(self.__di.spinStepPulse.value()))
    if self.__di.spinStepIdleDelay.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$1={}".format(self.__di.spinStepIdleDelay.value()))
      self.__grblCom.gcodePush("$1={}".format(self.__di.spinStepIdleDelay.value()))
    if self.__di.emStepPortInvert.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$2={}".format(self.__di.emStepPortInvert.getValue()))
      self.__grblCom.gcodePush("$2={}".format(self.__di.emStepPortInvert.getValue()))
    if self.__di.emDirectionPortInvert.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$3={}".format(self.__di.emDirectionPortInvert.getValue()))
      self.__grblCom.gcodePush("$3={}".format(self.__di.emDirectionPortInvert.getValue()))
    if self.__di.chkStepEnableInvert.objectName() in self.__changedParams:
      if self.__di.chkStepEnableInvert.isChecked():
        self.sig_config_changed.emit("$4=1")
        self.__grblCom.gcodePush("$4=1")
      else:
        self.sig_config_changed.emit("$4=0")
        self.__grblCom.gcodePush("$4=0")
    if self.__di.chkLimitPinsInvert.objectName() in self.__changedParams:
      if self.__di.chkLimitPinsInvert.isChecked():
        self.sig_config_changed.emit("$5=1")
        self.__grblCom.gcodePush("$5=1")
      else:
        self.sig_config_changed.emit("$5=0")
        self.__grblCom.gcodePush("$5=0")
    if self.__di.chkProbePinInvert.objectName() in self.__changedParams:
      if self.__di.chkProbePinInvert.isChecked():
        self.sig_config_changed.emit("$6=1")
        self.__grblCom.gcodePush("$6=1")
      else:
        self.sig_config_changed.emit("$6=0")
        self.__grblCom.gcodePush("$6=0")

    # Onglet 3 Unites
    if self.__di.lneStatusReport in self.__changedParams:
      self.sig_config_changed.emit("$10={}".format(self.__di.lneStatusReport.text()))
      self.__grblCom.gcodePush("$10={}".format(self.__di.lneStatusReport.text()))
    if self.__di.dsbJunctionDeviation.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$11={}".format(self.__di.dsbJunctionDeviation.value()))
      self.__grblCom.gcodePush("$11={}".format(self.__di.dsbJunctionDeviation.value()))
    if self.__di.dsbArcTolerance.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$12={}".format(self.__di.dsbArcTolerance.value()))
      self.__grblCom.gcodePush("$12={}".format(self.__di.dsbArcTolerance.value()))
    if self.__di.chkReportInches.objectName() in self.__changedParams:
      if self.__di.chkReportInches.isChecked():
        self.sig_config_changed.emit("$13=1")
        self.__grblCom.gcodePush("$13=1")
      else:
        self.sig_config_changed.emit("$13=0")
        self.__grblCom.gcodePush("$13=0")

    # Onglet 4 Limites
    if self.__di.chkSoftLimits.objectName() in self.__changedParams:
      if self.__di.chkSoftLimits.isChecked():
        self.sig_config_changed.emit("$20=1")
        self.__grblCom.gcodePush("$20=1")
      else:
        self.sig_config_changed.emit("$20=0")
        self.__grblCom.gcodePush("$20=0")
    if self.__di.chkHardLimits.objectName() in self.__changedParams:
      if self.__di.chkHardLimits.isChecked():
        self.sig_config_changed.emit("$21=1")
        self.__grblCom.gcodePush("$21=1")
      else:
        self.sig_config_changed.emit("$21=0")
        self.__grblCom.gcodePush("$21=0")
    if self.__di.chkHomingCycle.objectName() in self.__changedParams:
      if self.__di.chkHomingCycle.isChecked():
        self.sig_config_changed.emit("$22=1")
        self.__grblCom.gcodePush("$22=1")
      else:
        self.sig_config_changed.emit("$22=0")
        self.__grblCom.gcodePush("$22=0")
    if self.__di.emHomeDirInvert.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$23={}".format(self.__di.emHomeDirInvert.getValue()))
      self.__grblCom.gcodePush("$23={}".format(self.__di.emHomeDirInvert.getValue()))
    if self.__di.dsbHomingFeed.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$24={}".format(self.__di.dsbHomingFeed.value()))
      self.__grblCom.gcodePush("$24={}".format(self.__di.dsbHomingFeed.value()))
    if self.__di.dsbHomingSeek.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$25={}".format(self.__di.dsbHomingSeek.value()))
      self.__grblCom.gcodePush("$25={}".format(self.__di.dsbHomingSeek.value()))
    if self.__di.spinHomingDebounce.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$26={}".format(self.__di.spinHomingDebounce.value()))
      self.__grblCom.gcodePush("$26={}".format(self.__di.spinHomingDebounce.value()))
    if self.__di.dsbHomingPullOff.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$27={}".format(self.__di.dsbHomingPullOff.value()))
      self.__grblCom.gcodePush("$27={}".format(self.__di.dsbHomingPullOff.value()))

    # Onglet 5 Broche
    if self.__di.spinMaxSpindle.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$30={}".format(self.__di.spinMaxSpindle.value()))
      self.__grblCom.gcodePush("$30={}".format(self.__di.spinMaxSpindle.value()))
    if self.__di.spinMinSpindle.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$31={}".format(self.__di.spinMinSpindle.value()))
      self.__grblCom.gcodePush("$31={}".format(self.__di.spinMinSpindle.value()))
    if self.__di.chkLaserMode.objectName() in self.__changedParams:
      if self.__di.chkLaserMode.isChecked():
        self.sig_config_changed.emit("$32=1")
        self.__grblCom.gcodePush("$32=1")
      else:
        self.sig_config_changed.emit("$32=0")
        self.__grblCom.gcodePush("$32=0")

    # Onglet 6 Courses
    if self.__di.dsbStepsX.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$100={}".format(self.__di.dsbStepsX.value()))
      self.__grblCom.gcodePush("$100={}".format(self.__di.dsbStepsX.value()))
    if self.__di.dsbStepsY.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$101={}".format(self.__di.dsbStepsY.value()))
      self.__grblCom.gcodePush("$101={}".format(self.__di.dsbStepsY.value()))
    if self.__di.dsbStepsZ.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$102={}".format(self.__di.dsbStepsZ.value()))
      self.__grblCom.gcodePush("$102={}".format(self.__di.dsbStepsZ.value()))
    if self.__di.dsbStepsA.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$103={}".format(self.__di.dsbStepsA.value()))
      self.__grblCom.gcodePush("$103={}".format(self.__di.dsbStepsA.value()))
    if self.__di.dsbStepsB.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$104={}".format(self.__di.dsbStepsB.value()))
      self.__grblCom.gcodePush("$104={}".format(self.__di.dsbStepsB.value()))
    if self.__di.dsbStepsC.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$105={}".format(self.__di.dsbStepsC.value()))
      self.__grblCom.gcodePush("$105={}".format(self.__di.dsbStepsC.value()))
    if self.__di.dsbTravelX.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$130={}".format(self.__di.dsbTravelX.value()))
      self.__grblCom.gcodePush("$130={}".format(self.__di.dsbTravelX.value()))
    if self.__di.dsbTravelY.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$131={}".format(self.__di.dsbTravelY.value()))
      self.__grblCom.gcodePush("$131={}".format(self.__di.dsbTravelY.value()))
    if self.__di.dsbTravelZ.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$132={}".format(self.__di.dsbTravelZ.value()))
      self.__grblCom.gcodePush("$132={}".format(self.__di.dsbTravelZ.value()))
    if self.__di.dsbTravelA.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$133={}".format(self.__di.dsbTravelA.value()))
      self.__grblCom.gcodePush("$133={}".format(self.__di.dsbTravelA.value()))
    if self.__di.dsbTravelB.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$134={}".format(self.__di.dsbTravelB.value()))
      self.__grblCom.gcodePush("$134={}".format(self.__di.dsbTravelB.value()))
    if self.__di.dsbTravelC.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$135={}".format(self.__di.dsbTravelC.value()))
      self.__grblCom.gcodePush("$135={}".format(self.__di.dsbTravelC.value()))

    # Onglet 7 Vitesses
    if self.__di.dsbMaxRateX.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$110={}".format(self.__di.dsbMaxRateX.value()))
      self.__grblCom.gcodePush("$110={}".format(self.__di.dsbMaxRateX.value()))
    if self.__di.dsbMaxRateY.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$111={}".format(self.__di.dsbMaxRateY.value()))
      self.__grblCom.gcodePush("$111={}".format(self.__di.dsbMaxRateY.value()))
    if self.__di.dsbMaxRateZ.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$112={}".format(self.__di.dsbMaxRateZ.value()))
      self.__grblCom.gcodePush("$112={}".format(self.__di.dsbMaxRateZ.value()))
    if self.__di.dsbMaxRateA.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$113={}".format(self.__di.dsbMaxRateA.value()))
      self.__grblCom.gcodePush("$113={}".format(self.__di.dsbMaxRateA.value()))
    if self.__di.dsbMaxRateB.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$114={}".format(self.__di.dsbMaxRateB.value()))
      self.__grblCom.gcodePush("$114={}".format(self.__di.dsbMaxRateB.value()))
    if self.__di.dsbMaxRateC.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$115={}".format(self.__di.dsbMaxRateC.value()))
      self.__grblCom.gcodePush("$115={}".format(self.__di.dsbMaxRateC.value()))
    if self.__di.dsbAccelX.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$120={}".format(self.__di.dsbAccelX.value()))
      self.__grblCom.gcodePush("$120={}".format(self.__di.dsbAccelX.value()))
    if self.__di.dsbAccelY.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$121={}".format(self.__di.dsbAccelY.value()))
      self.__grblCom.gcodePush("$121={}".format(self.__di.dsbAccelY.value()))
    if self.__di.dsbAccelZ.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$122={}".format(self.__di.dsbAccelZ.value()))
      self.__grblCom.gcodePush("$122={}".format(self.__di.dsbAccelZ.value()))
    if self.__di.dsbAccelA.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$123={}".format(self.__di.dsbAccelA.value()))
      self.__grblCom.gcodePush("$123={}".format(self.__di.dsbAccelA.value()))
    if self.__di.dsbAccelB.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$124={}".format(self.__di.dsbAccelB.value()))
      self.__grblCom.gcodePush("$124={}".format(self.__di.dsbAccelB.value()))
    if self.__di.dsbAccelC.objectName() in self.__changedParams:
      self.sig_config_changed.emit("$125={}".format(self.__di.dsbAccelC.value()))
      self.__grblCom.gcodePush("$125={}".format(self.__di.dsbAccelC.value()))


  @pyqtSlot()
  def on_Discard(self):
    self.reject()


  @pyqtSlot()
  def on_Reset(self):
    self.__getGrblParams()


  @pyqtSlot()
  def on_ResetFactory(self):
    m = msgBox(
        title     = self.tr("Restore factory settings"),
        text      = self.tr("Are you sure?\nRestoring the factory settings restores all settings as they were when generating the Grbl firmware."),
        info      = self.tr("All modifications and adjustments made to this instance of Grbl will be permanently lost!"),
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
    if chk.checkState() == Qt.CheckState.Checked:
      chk.setText("True")
    else:
      chk.setText("False")
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # memorise que le parametre a change
    if not chk.objectName() in self.__changedParams:
      self.__changedParams.append(chk.objectName())

  @pyqtSlot(QSpinBox)
  @pyqtSlot(QDoubleSpinBox)
  def spinChange(self, spin):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # memorise que le parametre a change
    if not spin.objectName() in self.__changedParams:
      self.__changedParams.append(spin.objectName())


  @pyqtSlot(qwEditMask)
  def editMaskChange(self, em):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # memorise que le parametre a change
    if not em.objectName() in self.__changedParams:
      self.__changedParams.append(em.objectName())


  @pyqtSlot(QLineEdit)
  def textChange(self, lne: QLineEdit):
    self.__configChanged     = True
    self.__buttonApply.setEnabled(True)
    self.__buttonReset.setEnabled(True)
    # memorise que le parametre a change
    if not lne.objectName() in self.__changedParams:
      self.__changedParams.append(lne.objectName())






