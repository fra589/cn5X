# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice
from PyQt5.QtMultimedia import QAudio, QAudioOutput, QAudioFormat
from math import pi, sin
import struct

class cn5XBeeper():
  '''
  Emissions de bip sonores
  '''
  def __init__(self):
    super().__init__()

    format = QAudioFormat()
    format.setChannelCount(1)
    format.setSampleRate(22050)
    format.setSampleSize(16)
    format.setCodec("audio/pcm")
    format.setByteOrder(QAudioFormat.LittleEndian)
    format.setSampleType(QAudioFormat.SignedInt)

    self.output = QAudioOutput(format)
    self.buffer = QBuffer()
    self.data = QByteArray()


  def beep(self, frequence: int, duree: float, volume: int):
    '''
    Emission d'un beep sonore,
    La fréquence doit être comprise entre 20 et 20000Hz,
    La durée est exprimée en secondes ou fraction de secondes,
    Le volume est un entier compris entre 0 et 32767.
    '''
    # Arrêt si déjà actif
    if self.output.state() == QAudio.ActiveState:
      self.output.stop()
    if self.buffer.isOpen():
      self.buffer.close()
    # On génère le buffer de son
    '''
    create 2 seconds of data with 22050 samples per second,
    each sample being 16 bits (2 bytes)
    '''
    self.data.clear()
    sampleRate = self.output.format().sampleRate()
    for k in range(int((duree * sampleRate))):
      t = k / float(sampleRate)
      value = int(volume * sin(2 * pi * frequence * t))
      self.data.append(struct.pack("<h", value))

    self.buffer.setData(self.data)
    self.buffer.open(QIODevice.ReadOnly)
    self.buffer.seek(0)
    self.output.start(self.buffer)

