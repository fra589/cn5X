# -*- coding: UTF-8 -*-

import grblError

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
      errNum = grblOutput[6:]
      return "Erreur grbl N° " + str(errNum) + [txt for txt in grblError if txt[0] == errNum]
    elif grblOutput[0] == "<" and grblOutput[-1] == ">":
      print("{" + grblOutput[1:-1] + "}")

    return grblOutput
    pass
