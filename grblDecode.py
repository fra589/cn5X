# -*- coding: UTF-8 -*-

from grblError import grblError
from grblAlarm import grblAlarm
from grblSettings import grblSetting

class grblDecode:
  ''' Classe de décodage des réponses de GRBL '''
  def __init__(self, ui):
    self.lblPosX = ui.lblPosX
    self.lblPosY = ui.lblPosY
    self.lblPosZ = ui.lblPosZ
    self.lblPosA = ui.lblPosA
    self.lblPosB = ui.lblPosB
    self.ui = ui
    pass

  def setReply(self, grblOutput):

    print("<<" + grblOutput + ">>")

    if grblOutput[:5] == "Grbl ": # Grbl 1.1f ['$' for help] (Init string)
      self.ui.statusBar.showMessage(grblOutput.split('[')[0])
      return grblOutput

    elif grblOutput == "ok":
      return grblOutput
      pass

    elif grblOutput[:6] == "error:":
      errNum = int(float(grblOutput[6:]))
      return "Erreur grbl N° " + str(errNum) + " : " + grblError[errNum][1] + "\n>>> " + grblError[errNum][2]

    elif grblOutput[:6] == "alarm:":
      alarmNum = int(float(grblOutput[6:]))
      return "Alarme grbl N° " + str(alarmNum) + " : " + grblAlarm[alarmNum][1] + "\n>>> " + grblAlarm[alarmNum][2]

    elif grblOutput[0] == "$": # Setting output
      settingNum = int(float(grblOutput[1:].split('=')[0]))
      settingInfo = grblSetting (settingNum)
      return (grblOutput + " >> " + settingInfo)

    elif grblOutput[0] == "<" and grblOutput[-1] == ">":
      print("{" + grblOutput[1:-1] + "}")
      tblDecode = grblOutput[1:-1].split("|")
      for D in tblDecode:
        print("D = {" + D + "}")
        print("D[:5] = {" + D[:5] + "}")
        # Valid machin state : Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
        if D == "Idle":
          print("Machine Idle")
          pass
        elif D == "Run":
          pass
        elif D == "Hold":
          #- `Hold:0` Hold complete. Ready to resume.
          #- `Hold:1` Hold in-progress. Reset will throw an alarm.
          pass
        elif D == "Jog":
          pass
        elif D == "Alarm":
          pass
        elif D == "Door":
          #- `Door:0` Door closed. Ready to resume.
          #- `Door:1` Machine stopped. Door still ajar. Can't resume until closed.
          #- `Door:2` Door opened. Hold (or parking retract) in-progress. Reset will throw an alarm.
          #- `Door:3` Door closed and resuming. Restoring from park, if applicable. Reset will throw an alarm.
          pass
        elif D == "Check":
          pass
        elif D == "Home":
          pass
        elif D == "Sleep":
          pass
        # Machine position
        elif D[:5] == "MPos:":
          print("Position machine trouvée")
          tblPos = D[5:].split(",")
          self.lblPosX.setText('{:+0.3f}'.format(float(tblPos[0])))
          self.lblPosY.setText('{:+0.3f}'.format(float(tblPos[1])))
          self.lblPosZ.setText('{:+0.3f}'.format(float(tblPos[2])))
          self.lblPosA.setText('{:+0.3f}'.format(float(tblPos[3])))
          self.lblPosB.setText('{:+0.3f}'.format(float(tblPos[4])))

    return grblOutput
