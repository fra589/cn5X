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

from grblCommunicator import grblCommunicator

class grblJog():
  '''
  Envoie les ordres de mouvements de Jogging
  '''
  def __init__(self, comm: grblCommunicator):
    super().__init__()
    self.__grblCom = comm

  @pyqtSlot(float)
  def jogX(value):
    '''
    Déplacement relatif de "value" mm sur X
    '''
    cmdJog = "$J=G91X" + str(value)
    self.__grblCom.
    pass






