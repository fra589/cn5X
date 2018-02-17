# -*- coding: UTF-8 -*-

from PyQt5 import QtGui
from grblError import grblError
from grblAlarm import grblAlarm
from grblSettings import grblSetting

class grblDecode():
  '''
  Classe de décodage des réponses de GRBL :
  - Décode les reponses de Grbl,
  - Met à jour l'interface graphique.
  - Stocke des valeurs des paramètres décodés.
  '''
  def __init__(self, ui):
    self.ui = ui
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
    self.__etatArrosage = None
    self.__etatMachine = None

  def decodeGrblStatus(self, grblOutput):

    if grblOutput[0] != "<" or grblOutput[-1] != ">":
      return "decodeGrblStatus : erreur ! \n" + "[" + grblOutput + "] Status incorrect."

    tblDecode = grblOutput[1:-1].split("|")
    for D in tblDecode:
      ###print("D = {" + D + "}")
      if D in self.__validMachineState:
        if D != self.__etatMachine:
          self.ui.lblEtat.setText(D)
          self.__etatMachine = D
          if D =="Hold:0":
            self.ui.lblEtat.setToolTip("Hold complete. Ready to resume.")
          elif D =="Hold:1":
            self.ui.lblEtat.setToolTip("Hold in-progress. Reset will throw an alarm.")
          elif D =="Door:0":
            self.ui.lblEtat.setToolTip("Door closed. Ready to resume.")
          elif D =="Door:1":
            self.ui.lblEtat.setToolTip("Machine stopped. Door still ajar. Can't resume until closed.")
          elif D =="Door:2":
            self.ui.lblEtat.setToolTip("Door opened. Hold (or parking retract) in-progress. Reset will throw an alarm.")
          elif D =="Door:3":
            self.ui.lblEtat.setToolTip("Door closed and resuming. Restoring from park, if applicable. Reset will throw an alarm.")
          else:
            self.ui.lblEtat.setToolTip("")

      # Machine position MPos ($10=0 ou 2) ou WPos ($10=1 ou 3)?
      elif D[:5] == "MPos:":
        if not self.ui.mnu_MPos.isChecked():
          self.ui.mnu_MPos.setChecked(True)
        if self.ui.mnu_WPos.isChecked():
          self.ui.mnu_WPos.setChecked(False)
        tblPos = D[5:].split(",")
        self.ui.lblPosX.setText('{:+0.3f}'.format(float(tblPos[0]))); self.ui.lblPosX.setToolTip("Machine Position (MPos).")
        self.ui.lblPosY.setText('{:+0.3f}'.format(float(tblPos[1]))); self.ui.lblPosY.setToolTip("Machine Position (MPos).")
        self.ui.lblPosZ.setText('{:+0.3f}'.format(float(tblPos[2]))); self.ui.lblPosZ.setToolTip("Machine Position (MPos).")
        self.ui.lblPosA.setText('{:+0.3f}'.format(float(tblPos[3]))); self.ui.lblPosA.setToolTip("Machine Position (MPos).")
        self.ui.lblPosB.setText('{:+0.3f}'.format(float(tblPos[4]))); self.ui.lblPosB.setToolTip("Machine Position (MPos).")
        # TODO: 6ème axe.
        self.ui.lblPosC.setText('{:+0.3f}'.format(float("0")))

      elif D[:5] == "WPos:":
        if not self.ui.mnu_WPos.isChecked():
          self.ui.mnu_WPos.setChecked(True)
        if self.ui.mnu_MPos.isChecked():
          self.ui.mnu_MPos.setChecked(False)
        tblPos = D[5:].split(",")
        self.ui.lblPosX.setText('{:+0.3f}'.format(float(tblPos[0]))); self.ui.lblPosX.setToolTip("Working Position (WPos).")
        self.ui.lblPosY.setText('{:+0.3f}'.format(float(tblPos[1]))); self.ui.lblPosY.setToolTip("Working Position (WPos).")
        self.ui.lblPosZ.setText('{:+0.3f}'.format(float(tblPos[2]))); self.ui.lblPosZ.setToolTip("Working Position (WPos).")
        self.ui.lblPosA.setText('{:+0.3f}'.format(float(tblPos[3]))); self.ui.lblPosA.setToolTip("Working Position (WPos).")
        self.ui.lblPosB.setText('{:+0.3f}'.format(float(tblPos[4]))); self.ui.lblPosB.setToolTip("Working Position (WPos).")
        # TODO: 6ème axe.
        self.ui.lblPosC.setText('{:+0.3f}'.format(float("0")))

      elif D[:4] == "WCO:": # Work Coordinate Offset
        tblPos = D[4:].split(",")
        for I in range(len(tblPos)):
          self.__wco[I] = float(tblPos[I])
        self.ui.lblWcoX.setText('{:+0.3f}'.format(self.__wco[0]))
        self.ui.lblWcoY.setText('{:+0.3f}'.format(self.__wco[1]))
        self.ui.lblWcoZ.setText('{:+0.3f}'.format(self.__wco[2]))
        self.ui.lblWcoA.setText('{:+0.3f}'.format(self.__wco[3]))
        self.ui.lblWcoB.setText('{:+0.3f}'.format(self.__wco[4]))

      elif D[:3] == "Bf:": # Buffer State (Bf:15,128)
        tblValue = D[3:].split(",")
        self.ui.progressBufferState.setValue(int(tblValue[0]))
        self.ui.progressBufferState.setMaximum(int(tblValue[1]))
        self.ui.progressBufferState.setToolTip("Buffer stat : " + tblValue[0] + "/" + tblValue[1])

      elif D[:3] == "Ln:": # Line Number
        return D

      elif D[2:] == "F:": # Current Feed and Speed
        return D

      elif D[3:] == "FS:": # Current Feed and Speed
        return D

      elif D[3:] == "Pn:": # Input Pin State
        return D

      elif D[3:] == "Ov:": # Override Values
        return D

      elif D[2:] == "A:": # OverrideAccessory State
        return D


    return ""

  def decodeGrblResponse(self, grblOutput):

    if grblOutput == "ok":
      return grblOutput

    elif grblOutput[:6] == "error:":
      errNum = int(float(grblOutput[6:]))
      return "Erreur grbl N° " + str(errNum) + " : " + grblError[errNum][1] + ",\n" + grblError[errNum][2]

    elif grblOutput[:6] == "ALARM:":
      alarmNum = int(float(grblOutput[6:]))
      return "Alarme grbl N° " + str(alarmNum) + " : " + grblAlarm[alarmNum][1] + ",\n" + grblAlarm[alarmNum][2]

    else:
      return "Réponse Grbl inconnue : [" + grblOutput + "]"

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
        messages indicate the parameter data printout from a "$#" user query.
        '''
        num=int(grblOutput[2:4])
        values=grblOutput[5:-1].split(",")
        for I in range(5): # TODO: Traiter un nombre d'axes différent de 5
          self.__G5x[num][I] = float(values[I])
        if num == self.__G5actif:
          self.ui.lblG5xX.setText('{:+0.3f}'.format(self.__G5x[num][0]))
          self.ui.lblG5xY.setText('{:+0.3f}'.format(self.__G5x[num][1]))
          self.ui.lblG5xZ.setText('{:+0.3f}'.format(self.__G5x[num][2]))
          self.ui.lblG5xA.setText('{:+0.3f}'.format(self.__G5x[num][3]))
          self.ui.lblG5xB.setText('{:+0.3f}'.format(self.__G5x[num][4]))
          # TODO: 6ème axe
        if num == 92:
          self.ui.lblG92X.setText('{:+0.3f}'.format(self.__G5x[num][0]))
          self.ui.lblG92Y.setText('{:+0.3f}'.format(self.__G5x[num][1]))
          self.ui.lblG92Z.setText('{:+0.3f}'.format(self.__G5x[num][2]))
          self.ui.lblG92A.setText('{:+0.3f}'.format(self.__G5x[num][3]))
          self.ui.lblG92B.setText('{:+0.3f}'.format(self.__G5x[num][4]))
          # TODO: 6ème axe

      elif grblOutput[1:5] == "TLO:":
        ''' Tool length offset (for the default z-axis) '''
        self.__toolLengthOffset = float(grblOutput[5:-1])

      elif grblOutput[1:5] == "PRB:":
        ''' Coordinates of the last probing cycle, suffix :1 => Success '''
        self.__probeCoord = grblOutput[5:-1].split(",")

      elif grblOutput[:4] == "[GC:":
        '''
        traitement intérogation $G : G-code Parser State Message
        [GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0 S0]
        '''
        tblGcodeParser = grblOutput[4:-1].split(" ")
        for S in tblGcodeParser:
          if S in ["G54", "G55", "G56", "G57", "G58", "G59"]:
            # Préparation font pour modifier dynamiquement Bold/Normal
            font = QtGui.QFont()
            font.setFamily("LED Calculator")
            font.setPointSize(16)
            font.setWeight(75)
            self.ui.lblOffsetActif.setText("Offset {}".format(S))
            num=int(S[1:])
            if num != self.__G5actif:
              self.__G5actif = num
            if self.ui.lblG5xX.text() != '{:+0.3f}'.format(self.__G5x[num][0]):
              self.ui.lblG5xX.setText('{:+0.3f}'.format(self.__G5x[num][0]))
            if self.ui.lblG5xY.text() != '{:+0.3f}'.format(self.__G5x[num][1]):
              self.ui.lblG5xY.setText('{:+0.3f}'.format(self.__G5x[num][1]))
            if self.ui.lblG5xZ.text() != '{:+0.3f}'.format(self.__G5x[num][2]):
              self.ui.lblG5xZ.setText('{:+0.3f}'.format(self.__G5x[num][2]))
            if self.ui.lblG5xA.text() != '{:+0.3f}'.format(self.__G5x[num][3]):
              self.ui.lblG5xA.setText('{:+0.3f}'.format(self.__G5x[num][3]))
            if self.ui.lblG5xB.text() != '{:+0.3f}'.format(self.__G5x[num][4]):
              self.ui.lblG5xB.setText('{:+0.3f}'.format(self.__G5x[num][4]))
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
            if S == 'G17': self.ui.lblPlan.setToolTip(" Plan de travail = XY ")
            if S == 'G18': self.ui.lblPlan.setToolTip(" Plan de travail = ZX ")
            if S == 'G19': self.ui.lblPlan.setToolTip(" Plan de travail = YZ ")
          elif S in ["G20", "G21"]:
            self.ui.lblUnites.setText(S)
            if S == 'G20': self.ui.lblUnites.setToolTip(" Unités = pouce ")
            if S == 'G21': self.ui.lblUnites.setToolTip(" Unités = millimètre ")
          elif S in ["G90", "G91"]:
            self.ui.lblCoord.setText(S)
            if S == 'G90': self.ui.lblCoord.setToolTip(" Déplacement en coordonnées absolues ")
            if S == 'G91': self.ui.lblCoord.setToolTip(" Déplacement en coordonnées relatives ")
          elif S in ['G0', 'G1']:
            self.ui.lblDeplacements.setText(S)
            if S == 'G0': self.ui.lblDeplacements.setToolTip(" Déplacement en vitesse rapide ")
            if S == 'G1': self.ui.lblDeplacements.setToolTip(" Déplacement en vitesse travail ")
          elif S in ['G93', 'G94']:
            self.ui.lblVitesse.setText(S)
            if S == 'G93': self.ui.lblVitesse.setToolTip(" Mode vitesse inverse du temps ")
            if S == 'G94': self.ui.lblVitesse.setToolTip(" Mode vitesse en unités par minute ")
          elif S in ['M3', 'M4', 'M5']:
            self.ui.lblBroche.setText(S)
            if S == 'M3': self.ui.lblBroche.setToolTip(" Broche en sens horaire ")
            if S == 'M4': self.ui.lblBroche.setToolTip(" Broche en sens anti-horaire ")
            if S == 'M5': self.ui.lblBroche.setToolTip(" Broche arrêtée ")
          elif S in ['M7', 'M8', 'M78', 'M9']:
            self.ui.lblArrosage.setText(S)
            if S == 'M7':
              self.ui.lblArrosage.setToolTip(" Arrosage par gouttelettes ")
              self.ui.btnFloodM7.setButtonStatus(True)
              self.ui.btnFloodM8.setButtonStatus(False)
              self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M7"
            if S == 'M8':
              self.ui.lblArrosage.setToolTip(" Arrosage fluide ")
              self.ui.btnFloodM7.setButtonStatus(False)
              self.ui.btnFloodM8.setButtonStatus(True)
              self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M8"
            if S == 'M78':
              self.ui.lblArrosage.setToolTip(" Arrosage fluide ")
              self.ui.btnFloodM7.setButtonStatus(True)
              self.ui.btnFloodM8.setButtonStatus(True)
              self.ui.btnFloodM9.setButtonStatus(False)
              self.__etatArrosage = "M78"
            if S == 'M9':
              self.ui.lblArrosage.setToolTip(" Arrosage arrêté ")
              self.ui.btnFloodM7.setButtonStatus(False)
              self.ui.btnFloodM8.setButtonStatus(False)
              self.ui.btnFloodM9.setButtonStatus(True)
              self.__etatArrosage = "M9"
          elif S[:1] == "T":
            self.ui.lblOutil.setText(S)
            self.ui.lblOutil.setToolTip(" Outil numéro " + S[1:])
          elif S[:1] == "S":
            self.ui.lblRotation.setText(S)
            self.ui.lblRotation.setToolTip(" Vitesse de broche = " + S[1:] + " tours/mn")
          elif S[:1] == "F":
            self.ui.lblAvance.setText(S)
            self.ui.lblAvance.setToolTip(" Vitesse d'avance = " + S[1:])
          else:
            return("Status G-code Parser non reconnu : " + S)

        #return(str(tblGcodeParser))
      else:
        # Autre réponse [] ?
        return grblOutput
      pass

  def get_etatArrosage(self):
    return self.__etatArrosage

  def get_etatMachine(self):
    return self.__etatMachine
