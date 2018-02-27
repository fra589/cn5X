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

from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from grblCommunicator import grblCommunicator

class grblJog():
  '''
  Envoie les ordres de mouvements de Jogging
  A jog command will only be accepted when Grbl is in either the 'Idle' or 'Jog' states.
  '''
  def __init__(self, comm: grblCommunicator):
    super().__init__()
    self.__grblCom  = comm
    self.__jogSpeed = 500

  @pyqtSlot(float)
  def jogX(self, value):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur X '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = "$J=G91G21F{}X{}".format(self.__jogSpeed, value)
      self.__grblCom.addFiFo(cmdJog)
    else:
      print("Jogging impossible, status non compatible.")

  @pyqtSlot(float)
  def jogY(self, value):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur Y '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = "$J=G91G21F{}Y{}".format(self.__jogSpeed, value)
      self.__grblCom.addFiFo(cmdJog)
    else:
      print("Jogging impossible, status non compatible.")

  @pyqtSlot(float)
  def jogZ(self, value):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur Z '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = "$J=G91G21F{}Z{}".format(self.__jogSpeed, value)
      self.__grblCom.addFiFo(cmdJog)
    else:
      print("Jogging impossible, status non compatible.")

  @pyqtSlot(float)
  def jogA(self, value):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur A '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = "$J=G91G21F{}A{}".format(self.__jogSpeed, value)
      self.__grblCom.addFiFo(cmdJog)
    else:
      print("Jogging impossible, status non compatible.")

  @pyqtSlot(float)
  def jogB(self, value):
    ''' Déplacement relatif (G91) de "value" mm (G21) sur B '''
    if self.__grblCom.grblStatus() in ['Idle', 'Jog']:
      cmdJog = "$J=G91G21F{}B{}".format(self.__jogSpeed, value)
      self.__grblCom.addFiFo(cmdJog)
    else:
      print("Jogging impossible, status non compatible.")

  def jogCancel(self):
    print("self.__grblCom.clearStack()")
    self.__grblCom.clearStack()
    print("self.__grblCom.sendData(chr(0x85))")
    self.__grblCom.sendData(chr(0x85)) # Le bouton n'est plus enfoncé, envoi direct Jog Cancel





