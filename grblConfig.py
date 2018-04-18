# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X                                               '
'                                                                         '
' cn5X is free software: you can redistribute it and/or modify it         '
'  under the terms of the GNU General Public License as published by      '
' the Free Software Foundation, either version 3 of the License, or       '
' (at your option) any later version.                                     '
'                                                                         '
' cn5X is distributed in the hope that it will be useful, but             '
' WITHOUT ANY WARRANTY; without even the implied warranty of              '
' MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           '
' GNU General Public License for more details.                            '
'                                                                         '
' You should have received a copy of the GNU General Public License       '
' along with this program.  If not, see <http://www.gnu.org/licenses/>.   '
'                                                                         '
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from cn5X_config import *
from grblCom import grblCom
from dlgConfig import *
from compilOptions import grblCompilOptions

class grblConfig(QObject):
  ''' Classe assurant la gestion de la boite de dialogue de configuration de Grbl '''

  def __init__(self, grbl: grblCom):
    super().__init__()
    self.__dlgConfig = QDialog()
    self.__di = Ui_dlgConfig()
    self.__di.setupUi(self.__dlgConfig)

    self.__buttonDiscard = self.__di.buttonBox.addButton(QDialogButtonBox.Discard)
    self.__buttonApply   = self.__di.buttonBox.addButton(QDialogButtonBox.Apply)
    self.__buttonReset   = self.__di.buttonBox.addButton(QDialogButtonBox.Reset)
    self.__buttonFactory = self.__di.buttonBox.addButton("Reset factory", QDialogButtonBox.ActionRole)

    self.__buttonFactory.pressed.connect(self.on_Apply)
    self.__buttonReset.pressed.connect(self.on_Reset)
    self.__buttonFactory.pressed.connect(self.on_ResetFactory)

    self.__di.chkStepEnableInvert.stateChanged.connect(self.chkStepEnableInvertStateChange)
    self.__di.chkLimitPinsInvert.stateChanged.connect(self.chkLimitPinsInvertStateChange)
    self.__di.chkProbePinInvert.stateChanged.connect(self.chkProbePinInvertStateChange)
    self.__di.chkReportInches.stateChanged.connect(self.chkReportInchesStateChange)

    self.__grblCom = grbl
    self.__grblCom.sig_init.connect(self.on_sig_init)
    self.__grblCom.sig_config.connect(self.on_sig_config)


  def showDialog(self):
    self.__getGrblParams()
    reply = self.__dlgConfig.exec_()
    print("Reponse de la boite de dialogue = {}".format(reply))


  def __getGrblParams(self):
    self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET)     # Envoi Ctrl+X.
    self.__grblCom.gcodePush(CMD_GRBL_GET_BUILD_INFO)     # $I
    self.__grblCom.gcodePush(CMD_GRBL_GET_STARTUP_BLOCKS) # $N
    self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)       # $$


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
        self.__di.txtN0.setText(data.split("=")[1])
      elif data[:3] == "$N1":
        self.__di.txtN1.setText(data.split("=")[1])
    elif data[:5] == "[VER:":
      print(data)
      decodeVer=data.split(":")[1].split(".")
      self.__di.lblGrblDate.setText(decodeVer[2])
      self.__di.txtEEPROM.setText(data[1:-1].split(":")[2])
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


  @pyqtSlot()
  def on_Apply(self):
    pass


  @pyqtSlot()
  def on_Reset(self):
    self.__getGrblParams()


  @pyqtSlot()
  def on_ResetFactory(self):
    #boite de confirmation à faire
    self.__grblCom.gcodePush(CMD_GRBL_RESET_ALL_EEPROM)       # $RST=*
    self.__getGrblParams()


  @pyqtSlot(int)
  def chkStepEnableInvertStateChange(self, value: int):
    if value == Qt.Checked:
      self.__di.chkStepEnableInvert.setText("True")
    else:
      self.__di.chkStepEnableInvert.setText("False")


  @pyqtSlot(int)
  def chkLimitPinsInvertStateChange(self, value: int):
    if value == Qt.Checked:
      self.__di.chkLimitPinsInvert.setText("True")
    else:
      self.__di.chkLimitPinsInvert.setText("False")


  @pyqtSlot(int)
  def chkProbePinInvertStateChange(self, value: int):
    if value == Qt.Checked:
      self.__di.chkProbePinInvert.setText("True")
    else:
      self.__di.chkProbePinInvert.setText("False")


  @pyqtSlot(int)
  def chkReportInchesStateChange(self, value: int):
    if value == Qt.Checked:
      self.__di.chkReportInches.setText("True")
    else:
      self.__di.chkReportInches.setText("False")



