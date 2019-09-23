# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2019 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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
    self.__jogSpeed = DEFAULT_JOG_SPEED


  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent, float)
  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent, float, float)
  def on_jog(self, cnButton, e, jogDistance, maxTravel=0):
    '''
    Deplacement relatif (G91) de "jogDistance" mm (G21) sur axe defini par le nom du bouton
    si jogDistance != 0, si jogDistance = 0, déplacement en coordonnées machine jusqu'à
    la course maxi.
    '''
    axis = cnButton.name()[-1]  # L'axe est definit par le dernier caractere du nom du Bouton

    if jogDistance != 0:
      if cnButton.name()[-5:-1] == "Plus":
        value = jogDistance
      else:
        value = -jogDistance
      if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
        cmdJog = CMD_GRBL_JOG + "G91G21F{}{}{}".format(self.__jogSpeed, axis, value)
        self.__grblCom.gcodePush(cmdJog, COM_FLAG_NO_OK)

    elif maxTravel != 0:  # jogDistance == 0 & maxTravel !=0
      if cnButton.name()[-5:-1] == "Plus":
        value = 0
      else:
        value = -maxTravel
      if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
        cmdJog = CMD_GRBL_JOG + "G53F{}{}{}".format(self.__jogSpeed, axis, value)
        self.__grblCom.gcodePush(cmdJog, COM_FLAG_NO_OK)


  def jogCancel(self):
    self.__grblCom.clearCom()
    self.__grblCom.realTimePush(REAL_TIME_JOG_CANCEL) # Commande realtime Jog Cancel


  def setJogSpeed(self, speed: float):
    if speed > 0:
      self.__jogSpeed = speed
    else:
      self.__jogSpeed = DEFAULT_JOG_SPEED

