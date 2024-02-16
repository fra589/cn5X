# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file is part of cn5X++                                             '
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

from PyQt6.QtCore import QObject, QThread, QEventLoop, pyqtSignal, pyqtSlot
from cn5X_config import *

class grblStack():
  '''
  Gestionnaire de file d'attente du port serie.
  Stocke des couples (CommandeGrbl, flag), soit en mode FiFo (addFiFo()), soit en mode LiFo (addLiFo())
  et les renvoie dans l'ordre choisi avec la fonction pop().
  '''

  def __init__(self):
    self.__data = []

  def isEmpty(self):
    return len(self.__data) == 0

  def count(self):
    return len(self.__data)

  def addFiFo(self, item, flag = COM_FLAG_NO_FLAG):
    ''' Ajoute un element en mode FiFO, l'element ajoute sera le dernier a sortir
    '''
    self.__data.append((item, flag))

  def addLiFo(self, item, flag = COM_FLAG_NO_FLAG):
    ''' Ajoute un element en mode LiFO, l'element ajoute sera le premier a sortir
    '''
    self.__data.insert(0, (item, flag))

  def next(self):
    ''' Renvoie le prochain element de la Queue sans depiler (le supprimer) ou None si la liste est vide.
    '''
    if len(self.__data) > 0:
      return self.__data[0]
    else:
      return None

  def pop(self):
    ''' Depile et renvoie le premier element de la liste ou None si la liste est vide.
    '''
    if len(self.__data) > 0:
      return self.__data.pop(0)
    else:
      return None

  def clear(self):
    ''' Vide toute la pile
    '''
    self.__data.clear()
