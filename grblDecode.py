# -*- coding: UTF-8 -*-

from grblError import grblError
from grblAlarm import grblAlarm
from grblSettings import grblSetting

class grblDecode:
  ''' Classe de décodage des réponses de GRBL '''
  def __init__(self, ui):
    lblPosX = ui.lblPosX
    lblPosX = ui.lblPosX
    lblPosX = ui.lblPosX
    lblPosX = ui.lblPosX
    lblPosX = ui.lblPosX
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

    return grblOutput
    pass
