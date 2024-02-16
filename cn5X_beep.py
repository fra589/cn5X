# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_beep.py, is part of cn5X++                             '
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
from PyQt6.QtCore import QUrl #, QBuffer, QByteArray, QIODevice,
from PyQt6.QtMultimedia import QSoundEffect, QAudio, QAudioOutput, QAudioFormat
#from math import pi, sin
#import struct

class cn5XBeeper():
  '''
  Emissions de bip sonores
  '''
  def __init__(self):
    super().__init__()

    beepFile = os.path.join(os.path.dirname(__file__), "son/beep.wav")
    self.__beep = QSoundEffect()
    self.__beep.setSource(QUrl.fromLocalFile(beepFile))
    self.__beep.setLoopCount(1)


  def beep(self, volume: float):
    '''
    Emission d'un beep sonore depuis le fichier beep.wav
    '''
    # Arrêt si déjà actif
    if self.__beep.isPlaying():
      self.__beep.stop()

    # On ajuste le volume demandé
    self.__beep.setVolume(volume)

    # On joue le son
    self.__beep.play()
