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

import sys, os, time #, datetime
from PyQt5 import QtGui # QtCore, , QtWidgets
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from cn5X_config import *
from cnQPushButton import cnQPushButton
from grblCom import grblCom

class grblJog():
  '''
  Envoie les ordres de mouvements de Jogging
  A jog command will only be accepted when Grbl is in either the 'Idle' or 'Jog' states.
  '''
  def __init__(self, comm: grblCom):
    super().__init__()
    self.__grblCom  = comm


  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent, float)
  def on_jog(self, cnButton, e, jogDistance):

    axis = cnButton.name()[-1]           # L'axe est définit par le dernier caractère du nom du Bouton
    if cnButton.name()[-5:-1] == "Plus": #
      if jogDistance == 0:
        value = 0.0125
      else:
        value = jogDistance
    else:
      if jogDistance == 0:
        value = -0.0125
      else:
        value = -jogDistance

    if jogDistance == 0:
      # On envoie des petits mouvements equivalent à 1 pas moteur tant que le bouton est enfoncé
      jogDelay = JOG_REPEAT_DELAY
      while cnButton.isMouseDown():
        self.doJog(axis, value)
        QCoreApplication.processEvents()
        time.sleep(jogDelay)
        if jogDelay == JOG_REPEAT_DELAY: jogDelay = JOG_REPEAT_SPEED
      self.jogCancel()
    else:
      self.doJog(axis, value)


  def doJog(self, axis: str, value: float):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur axe axis '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = CMD_GRBL_JOG + "G91G21F{}{}{}".format(JOG_SPEED, axis, value)
      self.__grblCom.gcodePush(cmdJog, "NO_OK")
    else:
      #print("Jogging impossible, status Grbl non compatible.")
      pass


  def jogCancel(self):
    self.__grblCom.clearCom()
    self.__grblCom.realTimePush(REAL_TIME_JOG_CANCEL) # Commande realtime Jog Cancel









