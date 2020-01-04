# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
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
'                                                                         '
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from PyQt5 import QtGui
from PyQt5 import QtWidgets, QtCore #, QtGui,
from PyQt5.QtCore import QCoreApplication, QObject
from grblError import grblError
from grblAlarm import grblAlarm
from grblSettings import grblSetting
from speedOverrides import *
from grblCom import grblCom


class grblDecode(QObject):
  '''
  Classe de decodage des reponses de GRBL :
  - Decode les reponses de Grbl,
  - Met a jour l'interface graphique.
  - Stocke des valeurs des parametres decodes.
  '''
  def __init__(self, ui, log, grbl: grblCom):
    super().__init__()
    self.ui = ui
    self.log = log
    self.__grblCom = grbl
    self.__nbAxis = DEFAULT_NB_AXIS
    self.__validMachineState = ['Idle', 'Run', 'Hold:0', 'Hold:1', 'Jog', 'Alarm', 'Door:0', 'Door:1', 'Door:2', 'Door:3', 'Check', 'Home', 'Sleep']
    self.__validG5x = ["G28", "G30", "G54","G55","G56","G57","G58","G59", "G92"]
    self.__G5actif = 54
    self.__G5x={
      28: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      30: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      54: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      55: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      56: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      57: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      58: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      59: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
      92: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    self.__toolLengthOffset = 0
    self.__probeCoord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.__wco = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.__wpos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.__mpos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.__etatArrosage = None
    self.__etatMachine = None
    self.__getNextStatusOutput = False
    self.__getNextGCodeParams = False
    self.__getNextGCodeState = False


  def getG5actif(self):
    return "G{}".format(self.__G5actif)


  def setNbAxis(self, val: int):
    if val < 3 or val > 6:
      raise RuntimeError(self.tr("Le nombre d'axes doit etre compris entre 3 et 6 !"))
    self.__nbAxis = val


  def getNextStatus(self):
    self.__getNextStatusOutput = True


  def getNextGCodeParams(self):
    self.__getNextGCodeParams = True


  def getNextGCodeState(self):
    self.__getNextGCodeState = True


  def decodeGrblStatus(self, grblOutput):

    if grblOutput[0] != "<" or grblOutput[-1] != ">":
      return self.tr("decodeGrblStatus : erreur ! \n[{}] Status incorrect.").format(grblOutput)

    # Affiche la chaine complette dans la barrs de status self.__statusText
    self.ui.statusBar.showMessage("{} + {}".format(self.__grblCom.grblVersion(), grblOutput))

    flagPn = False
    tblDecode = grblOutput[1:-1].split("|")
    for D in tblDecode:
      ###print("D = {" + D + "}")
      if D in self.__validMachineState:
        if D != self.__etatMachine:
          self.ui.lblEtat.setText(D)
          self.__etatMachine = D
          if D == GRBL_STATUS_IDLE:
            if self.ui.btnStart.getButtonStatus():    self.ui.btnStart.setButtonStatus(False)
            if self.ui.btnPause.getButtonStatus():    self.ui.btnPause.setButtonStatus(False)
            if not self.ui.btnStop.getButtonStatus(): self.ui.btnStop.setButtonStatus(True)
            self.ui.lblEtat.setToolTip("Grbl is waiting for work.")
          elif D ==GRBL_STATUS_HOLD0:
            if self.ui.btnStart.getButtonStatus():    self.ui.btnStart.setButtonStatus(False)
            if not self.ui.btnPause.getButtonStatus():    self.ui.btnPause.setButtonStatus(True)
            if self.ui.btnStop.getButtonStatus(): self.ui.btnStop.setButtonStatus(False)
            self.ui.lblEtat.setToolTip("Hold complete. Ready to resume.")
          elif D ==GRBL_STATUS_HOLD1:
            if self.ui.btnStart.getButtonStatus():    self.ui.btnStart.setButtonStatus(False)
            if not self.ui.btnPause.getButtonStatus():    self.ui.btnPause.setButtonStatus(True)
            if self.ui.btnStop.getButtonStatus(): self.ui.btnStop.setButtonStatus(False)
            self.ui.lblEtat.setToolTip("Hold in-progress. Reset will throw an alarm.")
          elif D =="Door:0":
            self.ui.lblEtat.setToolTip("Door closed. Ready to resume.")
          elif D =="Door:1":
            self.ui.lblEtat.setToolTip("Machine stopped. Door still ajar. Can't resume until closed.")
          elif D =="Door:2":
            self.ui.lblEtat.setToolTip("Door opened. Hold (or parking retract) in-progress. Reset will throw an alarm.")
          elif D =="Door:3":
            self.ui.lblEtat.setToolTip("Door closed and resuming. Restoring from park, if applicable. Reset will throw an alarm.")
          elif D == GRBL_STATUS_RUN:
            if not self.ui.btnStart.getButtonStatus():    self.ui.btnStart.setButtonStatus(True)
            if self.ui.btnPause.getButtonStatus():    self.ui.btnPause.setButtonStatus(False)
            if self.ui.btnStop.getButtonStatus(): self.ui.btnStop.setButtonStatus(False)
            self.ui.lblEtat.setToolTip("Grbl running...")
          elif D == GRBL_STATUS_JOG:
            self.ui.lblEtat.setToolTip("Grbl jogging...")
          elif D == GRBL_STATUS_ALARM:
            self.ui.lblEtat.setToolTip("Grbl Alarm! see Grbl communication.")
          elif D == GRBL_STATUS_HOME:
            self.ui.lblEtat.setToolTip("Grbl homing, wait for finish...")
          else:
            self.ui.lblEtat.setToolTip("")

      # Machine position MPos ($10=0 ou 2) ou WPos ($10=1 ou 3)?
      elif D[:5] == "MPos:":
        # Mémorise la dernière position machine reçue
        tblPos = D[5:].split(",")
        for I in range(len(tblPos)):
          self.__mpos[I] = float(tblPos[I])
          self.__wpos[I] = float(tblPos[I]) - self.__wco[I]
        # Met à jour l'interface
        if not self.ui.mnu_MPos.isChecked():
          self.ui.mnu_MPos.setChecked(True)
        if self.ui.mnu_WPos.isChecked():
          self.ui.mnu_WPos.setChecked(False)
        tblPos = D[5:].split(",")
        self.ui.lblPosX.setText('{:+0.3f}'.format(float(tblPos[0]))); self.ui.lblPosX.setToolTip("Machine Position (MPos).")
        self.ui.lblPosY.setText('{:+0.3f}'.format(float(tblPos[1]))); self.ui.lblPosY.setToolTip("Machine Position (MPos).")
        self.ui.lblPosZ.setText('{:+0.3f}'.format(float(tblPos[2]))); self.ui.lblPosZ.setToolTip("Machine Position (MPos).")
        if self.__nbAxis > 3:
          self.ui.lblPosA.setText('{:+0.3f}'.format(float(tblPos[3]))); self.ui.lblPosA.setToolTip("Machine Position (MPos).")
        else:
          self.ui.lblPosA.setText("-")
        if self.__nbAxis > 4:
          self.ui.lblPosB.setText('{:+0.3f}'.format(float(tblPos[4]))); self.ui.lblPosB.setToolTip("Machine Position (MPos).")
        else:
          self.ui.lblPosB.setText("-")
        if self.__nbAxis > 5:
          self.ui.lblPosC.setText('{:+0.3f}'.format(float(tblPos[5]))); self.ui.lblPosB.setToolTip("Machine Position (MPos).")
        else:
          self.ui.lblPosC.setText("-")

      elif D[:5] == "WPos:":
        # Mémorise la dernière position de travail reçue
        tblPos = D[5:].split(",")
        for I in range(len(tblPos)):
          self.__wpos[I] = float(tblPos[I])
          self.__mpos[I] = float(tblPos[I]) + self.__wco[I]
        # Met à jour l'interface
        if not self.ui.mnu_WPos.isChecked():
          self.ui.mnu_WPos.setChecked(True)
        if self.ui.mnu_MPos.isChecked():
          self.ui.mnu_MPos.setChecked(False)
        tblPos = D[5:].split(",")
        self.ui.lblPosX.setText('{:+0.3f}'.format(float(tblPos[0]))); self.ui.lblPosX.setToolTip("Working Position (WPos).")
        self.ui.lblPosY.setText('{:+0.3f}'.format(float(tblPos[1]))); self.ui.lblPosY.setToolTip("Working Position (WPos).")
        self.ui.lblPosZ.setText('{:+0.3f}'.format(float(tblPos[2]))); self.ui.lblPosZ.setToolTip("Working Position (WPos).")
        if self.__nbAxis > 3:
          self.ui.lblPosA.setText('{:+0.3f}'.format(float(tblPos[3]))); self.ui.lblPosA.setToolTip("Working Position (WPos).")
        else:
          self.ui.lblPosA.setText("-")
        if self.__nbAxis > 4:
          self.ui.lblPosB.setText('{:+0.3f}'.format(float(tblPos[4]))); self.ui.lblPosB.setToolTip("Working Position (WPos).")
        else:
          self.ui.lblPosB.setText("-")
        if self.__nbAxis > 5:
          self.ui.lblPosC.setText('{:+0.3f}'.format(float(tblPos[5]))); self.ui.lblPosB.setToolTip("Working Position (WPos).")
        else:
          self.ui.lblPosC.setText("-")

      elif D[:4] == "WCO:": # Work Coordinate Offset
        tblPos = D[4:].split(",")
        for I in range(len(tblPos)):
          self.__wco[I] = float(tblPos[I])
        self.ui.lblWcoX.setText('{:+0.3f}'.format(self.__wco[0]))
        self.ui.lblWcoY.setText('{:+0.3f}'.format(self.__wco[1]))
        self.ui.lblWcoZ.setText('{:+0.3f}'.format(self.__wco[2]))
        if self.__nbAxis > 3:
          self.ui.lblWcoA.setText('{:+0.3f}'.format(self.__wco[3]))
        else:
          self.ui.lblWcoA.setText("-")
        if self.__nbAxis > 4:
          self.ui.lblWcoB.setText('{:+0.3f}'.format(self.__wco[4]))
        else:
          self.ui.lblWcoB.setText("-")
        if self.__nbAxis > 5:
          self.ui.lblWcoC.setText('{:+0.3f}'.format(self.__wco[5]))
        else:
          self.ui.lblWcoC.setText("-")

      elif D[:3] == "Bf:": # Buffer State (Bf:15,128)
        tblValue = D[3:].split(",")
        self.ui.progressBufferState.setValue(int(tblValue[0]))
        self.ui.progressBufferState.setMaximum(int(tblValue[1]))
        self.ui.progressBufferState.setToolTip("Buffer stat : " + tblValue[0] + "/" + tblValue[1])

      elif D[:3] == "Ov:": # Override Values for feed, rapids, and spindle
        values = D.split(':')[1].split(',')
        # Avance de travail
        if int(self.ui.lblAvancePourcent.text()[:-1]) != int(values[0]):
          adjustFeedOverride(int(values[0]), int(self.ui.lblAvancePourcent.text()[:-1]), self.__grblCom)
        # Avance rapide
        if values[1] == 25:
          self.ui.rbRapid025.setChecked(True)
        if values[1] == 50:
          self.ui.rbRapid050.setChecked(True)
        if values[1] == 25:
          self.ui.rbRapid100.setChecked(True)
        # Ajuste la vitesse de broche
        if int(self.ui.lblBrochePourcent.text()[:-1]) != int(values[2]):
          adjustSpindleOverride(int(values[2]), int(self.ui.lblBrochePourcent.text()[:-1]), self.__grblCom)

      elif D[:3] == "Pn:": # Input Pin State
        flagPn = True
        triggered = D[3:]
        for L in ['X', 'Y', 'Z', 'A', 'B', 'C', 'P', 'D', 'H', 'R', 'S']:
          if L in triggered:
            exec("self.ui.cnLed" + L + ".setLedStatus(True)")
          else:
            exec("self.ui.cnLed" + L + ".setLedStatus(False)")

      '''
      elif D[:3] == "Ln:": # Line Number
        return D

      elif D[2:] == "F:": # Current Feed and Speed
        return D

      elif D[3:] == "FS:": # Current Feed and Speed
        return D
      '''
      '''
      elif D[2:] == "A:": # OverrideAccessory State
        return D
      '''
    if not flagPn:
      # Eteint toute les leds. Si on a pas trouve la chaine Pn:, c'est que toute les leds sont eteintes.
      for L in ['X', 'Y', 'Z', 'A', 'B', 'C', 'P', 'D', 'H', 'R', 'S']:
        exec("self.ui.cnLed" + L + ".setLedStatus(False)")


    if self.__getNextStatusOutput:
      self.__getNextStatusOutput = False
      return grblOutput
    else:
      return ""

  def decodeGrblResponse(self, grblOutput):

    if grblOutput == "ok":
      return grblOutput

    elif grblOutput[:6] == "error:":
      errNum = int(float(grblOutput[6:]))
      return self.tr("Erreur grbl No {} : {},\n{}").format(str(errNum), grblError[errNum][1], grblError[errNum][2])

    elif grblOutput[:6] == "ALARM:":
      alarmNum = int(float(grblOutput[6:]))
      return self.tr("Alarme grbl No {} : {},\n{}").format(str(alarmNum), grblAlarm[alarmNum][1], grblAlarm[alarmNum][2])

    else:
      return self.tr("Reponse Grbl inconnue : [{}]").format(grblOutput)


  def errorMessage(self, errNum: int):
    return "error:{}: {},\n{}".format(str(errNum), grblError[errNum][1], grblError[errNum][2])


  def alarmMessage(self, alarmNum: int):
    return "ALARM:{}: {},\n{}".format(str(alarmNum), grblAlarm[alarmNum][1], grblAlarm[alarmNum][2])


  def decodeGrblData(self, grblOutput):

    if grblOutput[:1] == "$": # Setting output
      if grblOutput[:2] == "$N": # startup blocks
        return grblOutput
      else: # Pure setting output
        settingNum = int(float(grblOutput[1:].split('=')[0]))
        settingInfo = grblSetting(settingNum)
        return (grblOutput + " >> " + settingInfo)

    elif grblOutput[:1] == "[" and grblOutput[-1:] == "]":
      ''' Push Messages: '''
      if grblOutput[1:4] in self.__validG5x: # ["G28", "G30", "G54","G55","G56","G57","G58","G59", "G92"]
        '''
        messages indicate the parameter data printout from a "$#" (CMD_GRBL_GET_GCODE_PARAMATERS) user query.
        '''
        num=int(grblOutput[2:4])
        values=grblOutput[5:-1].split(",")
        for I in range(6):
          if I < self.__nbAxis:
            self.__G5x[num][I] = float(values[I])
          else:
            self.__G5x[num][I] = float("0")
        if num == self.__G5actif:
          self.ui.lblG5xX.setText('{:+0.3f}'.format(self.__G5x[num][0]))
          self.ui.lblG5xY.setText('{:+0.3f}'.format(self.__G5x[num][1]))
          self.ui.lblG5xZ.setText('{:+0.3f}'.format(self.__G5x[num][2]))
          if self.__nbAxis > 3:
            self.ui.lblG5xA.setText('{:+0.3f}'.format(self.__G5x[num][3]))
          else:
            self.ui.lblG5xA.setText("-")
          if self.__nbAxis > 4:
            self.ui.lblG5xB.setText('{:+0.3f}'.format(self.__G5x[num][4]))
          else:
            self.ui.lblG5xB.setText("-")
          if self.__nbAxis > 5:
            self.ui.lblG5xC.setText('{:+0.3f}'.format(self.__G5x[num][5]))
          else:
            self.ui.lblG5xC.setText("-")
        if num == 92:
          self.ui.lblG92X.setText('{:+0.3f}'.format(self.__G5x[num][0]))
          self.ui.lblG92Y.setText('{:+0.3f}'.format(self.__G5x[num][1]))
          self.ui.lblG92Z.setText('{:+0.3f}'.format(self.__G5x[num][2]))
          if self.__nbAxis > 3:
            self.ui.lblG92A.setText('{:+0.3f}'.format(self.__G5x[num][3]))
          else:
            self.ui.lblG92A.setText("-")
          if self.__nbAxis > 4:
            self.ui.lblG92B.setText('{:+0.3f}'.format(self.__G5x[num][4]))
          else:
            self.ui.lblG92B.setText("-")
          if self.__nbAxis > 5:
            self.ui.lblG92C.setText('{:+0.3f}'.format(self.__G5x[num][5]))
          else:
            self.ui.lblG92C.setText("-")
        # renvoie le résultat si $# demandé dans par l'utilisateur
        if self.__getNextGCodeParams:
          return grblOutput

      elif grblOutput[1:5] == "TLO:":
        ''' Tool length offset (for the default z-axis) '''
        self.__toolLengthOffset = float(grblOutput[5:-1])
        # renvoie le résultat si $# demandé dans par l'utilisateur
        if self.__getNextGCodeParams:
          return grblOutput

      elif grblOutput[1:5] == "PRB:":
        ''' Coordinates of the last probing cycle, suffix :1 => Success '''
        self.__probeCoord = grblOutput[5:-1].split(",")
        # renvoie le résultat si $# demandé dans par l'utilisateur
        if self.__getNextGCodeParams:
          self.__getNextGCodeParams = False # L'envoi du résultat de $# est complet
          return grblOutput

      elif grblOutput[:4] == "[GC:":
        '''
        traitement interogation $G : G-code Parser State Message
        [GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0 S0]
        '''
        tblGcodeParser = grblOutput[4:-1].split(" ")
        for S in tblGcodeParser:
          if S in ["G54", "G55", "G56", "G57", "G58", "G59"]:
            # Preparation font pour modifier dynamiquement Bold/Normal
            font = QtGui.QFont()
            font.setFamily("LED Calculator")
            font.setPointSize(16)
            font.setWeight(75)
            self.ui.lblOffsetActif.setText("Offset {}".format(S))
            num=int(S[1:])
            if num != self.__G5actif:
              self.__G5actif = num
            for N, lbl in [
              [54, self.ui.lblG54],
              [55, self.ui.lblG55],
              [56, self.ui.lblG56],
              [57, self.ui.lblG57],
              [58, self.ui.lblG58],
              [59, self.ui.lblG59]
            ]:
              if N == num:
                lbl.setStyleSheet("background-color:  rgb(0, 0, 63); color:rgb(248, 255, 192);")
                font.setBold(True)
                lbl.setFont(font)
              else:
                lbl.setStyleSheet("background-color: rgb(248, 255, 192); color: rgb(0, 0, 63);")
                font.setBold(False)
                lbl.setFont(font)
          elif S in ["G17", "G18", "G19"]:
            self.ui.lblPlan.setText(S)
            if S == 'G17': self.ui.lblPlan.setToolTip(self.tr(" Plan de travail = XY "))
            if S == 'G18': self.ui.lblPlan.setToolTip(self.tr(" Plan de travail = ZX "))
            if S == 'G19': self.ui.lblPlan.setToolTip(self.tr(" Plan de travail = YZ "))
          elif S in ["G20", "G21"]:
            self.ui.lblUnites.setText(S)
            if S == 'G20': self.ui.lblUnites.setToolTip(self.tr(" Unites = pouce "))
            if S == 'G21': self.ui.lblUnites.setToolTip(self.tr(" Unites = millimetre "))
          elif S in ["G90", "G91"]:
            self.ui.lblCoord.setText(S)
            if S == 'G90': self.ui.lblCoord.setToolTip(self.tr(" Deplacement en coordonnees absolues "))
            if S == 'G91': self.ui.lblCoord.setToolTip(self.tr(" Deplacement en coordonnees relatives "))
          elif S in ['G0', 'G1', 'G2', 'G3']:
            self.ui.lblDeplacements.setText(S)
            if S == 'G0': self.ui.lblDeplacements.setToolTip(self.tr(" Deplacement en vitesse rapide "))
            if S == 'G1': self.ui.lblDeplacements.setToolTip(self.tr(" Deplacement en vitesse travail "))
            if S == 'G2': self.ui.lblDeplacements.setToolTip(self.tr(" Interpolation circulaire sens horaire en vitesse travail "))
            if S == 'G3': self.ui.lblDeplacements.setToolTip(self.tr(" Interpolation circulaire sens anti-horaire en vitesse travail "))
          elif S in ['G93', 'G94']:
            self.ui.lblVitesse.setText(S)
            if S == 'G93': self.ui.lblVitesse.setToolTip(self.tr(" Mode vitesse inverse du temps "))
            if S == 'G94': self.ui.lblVitesse.setToolTip(self.tr(" Mode vitesse en unites par minute "))
          elif S in ['M3', 'M4', 'M5']:
            self.ui.lblBroche.setText(S)
            if S == 'M3':
              self.ui.lblBroche.setToolTip(self.tr(" Broche en sens horaire "))
              if not self.ui.btnSpinM3.getButtonStatus(): self.ui.btnSpinM3.setButtonStatus(True)
              if self.ui.btnSpinM4.getButtonStatus():     self.ui.btnSpinM4.setButtonStatus(False)
              if self.ui.btnSpinM5.getButtonStatus():     self.ui.btnSpinM5.setButtonStatus(False)
              if not self.ui.btnSpinM3.isEnabled(): self.ui.btnSpinM3.setEnabled(True)  # Activation bouton M3
              if self.ui.btnSpinM4.isEnabled(): self.ui.btnSpinM4.setEnabled(False)     # Interdit un changement de sens de rotation direct
            if S == 'M4':
              self.ui.lblBroche.setToolTip(self.tr(" Broche en sens anti-horaire "))
              if self.ui.btnSpinM3.getButtonStatus():     self.ui.btnSpinM3.setButtonStatus(False)
              if not self.ui.btnSpinM4.getButtonStatus(): self.ui.btnSpinM4.setButtonStatus(True)
              if self.ui.btnSpinM5.getButtonStatus():     self.ui.btnSpinM5.setButtonStatus(False)
              if self.ui.btnSpinM3.isEnabled(): self.ui.btnSpinM3.setEnabled(False)     # Interdit un changement de sens de rotation direct
              if not self.ui.btnSpinM4.isEnabled(): self.ui.btnSpinM4.setEnabled(True)  # Activation bouton M4
            if S == 'M5':
              self.ui.lblBroche.setToolTip(self.tr(" Broche arretee "))
              if self.ui.btnSpinM3.getButtonStatus():     self.ui.btnSpinM3.setButtonStatus(False)
              if self.ui.btnSpinM4.getButtonStatus():     self.ui.btnSpinM4.setButtonStatus(False)
              if not self.ui.btnSpinM5.getButtonStatus(): self.ui.btnSpinM5.setButtonStatus(True)
              if not self.ui.btnSpinM3.isEnabled(): self.ui.btnSpinM3.setEnabled(True)  # Activation bouton M3
              if not self.ui.btnSpinM4.isEnabled(): self.ui.btnSpinM4.setEnabled(True)  # Activation bouton M4
          elif S in ['M7', 'M8', 'M78', 'M9']:
            self.ui.lblArrosage.setText(S)
            if S == 'M7':
              self.ui.lblArrosage.setToolTip(self.tr(" Arrosage par gouttelettes "))
              if not self.ui.btnFloodM7.getButtonStatus(): self.ui.btnFloodM7.setButtonStatus(True)
              if self.ui.btnFloodM8.getButtonStatus():     self.ui.btnFloodM8.setButtonStatus(False)
              if self.ui.btnFloodM9.getButtonStatus():     self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M7"
            if S == 'M8':
              self.ui.lblArrosage.setToolTip(self.tr(" Arrosage fluide "))
              if self.ui.btnFloodM7.getButtonStatus():     self.ui.btnFloodM7.setButtonStatus(False)
              if not self.ui.btnFloodM8.getButtonStatus(): self.ui.btnFloodM8.setButtonStatus(True)
              if self.ui.btnFloodM9.getButtonStatus():     self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M8"
            if S == 'M78':
              self.ui.lblArrosage.setToolTip(self.tr(" Arrosage goutelettes + fluide "))
              if not self.ui.btnFloodM7.getButtonStatus(): self.ui.btnFloodM7.setButtonStatus(True)
              if not self.ui.btnFloodM8.getButtonStatus(): self.ui.btnFloodM8.setButtonStatus(True)
              if self.ui.btnFloodM9.getButtonStatus():     self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M78"
            if S == 'M9':
              self.ui.lblArrosage.setToolTip(self.tr(" Arrosage arrete "))
              if self.ui.btnFloodM7.getButtonStatus():     self.ui.btnFloodM7.setButtonStatus(False)
              if self.ui.btnFloodM8.getButtonStatus():     self.ui.btnFloodM8.setButtonStatus(False)
              if not self.ui.btnFloodM9.getButtonStatus(): self.ui.btnFloodM9.setButtonStatus(True)
              self.__etatArrosage = "M9"
          elif S[:1] == "T":
            self.ui.lblOutil.setText(S)
            self.ui.lblOutil.setToolTip(self.tr(" Outil numero {}").format(S[1:]))
          elif S[:1] == "S":
            self.ui.lblRotation.setText(S)
            self.ui.lblRotation.setToolTip(self.tr(" Vitesse de broche = {} tours/mn").format(S[1:]))
          elif S[:1] == "F":
            self.ui.lblAvance.setText(S)
            self.ui.lblAvance.setToolTip(self.tr(" Vitesse d'avance = ").format(S[1:]))
          else:
            return(self.tr("Status G-code Parser non reconnu dans {} : {}").format(grblOutput, S))
        # renvoie le résultat si $G demandé dans par l'utilisateur
        if self.__getNextGCodeState:
          self.__getNextGCodeState = False
          return grblOutput
      else:
        # Autre reponse [] ?
        return grblOutput
    else:
      # Autre reponse ?
      if grblOutput != "": self.log(logSeverity.info.value, self.tr("Reponse Grbl non decodee : [{}]").format(grblOutput))
      return grblOutput


  def get_etatArrosage(self):
    return self.__etatArrosage


  def get_etatMachine(self):
    return self.__etatMachine


  def wco(self):
    return self.__wco


  def wpos(self, axis=None):
    return self.__wpos


  def mpos(self, axis=None):
    if not (axis is None):
      return self.__mpos[axis]
    else:
      return self.__mpos


