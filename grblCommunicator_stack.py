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

from PyQt5.QtCore import QObject, QThread, QEventLoop, pyqtSignal, pyqtSlot

class grblSerialStack(QObject):
  ''' Gestionnaire de file d'attente du port série
  '''
  def __init__(self):
    self.__data = []

  def isEmpty(self):
    return len(self.__data) == 0

  def count(self):
    return len(self.__data)

  def addFiFo(self, item):
    '''
    Ajoute un élément en mode FiFO, l'élément ajouté sera le dernier à sortir
    '''
    self.__data.append(item)

  def addLiFo(self, item):
    ''' Ajoute un élément en mode LiFO, l'élément ajouté sera le premier à sortir
    '''
    self.__data.insert(0, item)

  def nextValue(self):
    ''' Renvoie le prochain élément de la Queue sans dépiler (le supprimer) ou None si la liste est vide.
    '''
    if len(self.__data) > 0:
      return self.__data[0]
    else:
      return None

  def deQueue(self):
    ''' Dépile et renvoie le premier élément de la liste ou None si la liste est vide.
    '''
    if len(self.__data) > 0:
      return self.__data.pop(0)
    else:
      return None

  def clear(self):
    ''' Vide toute la pile
    '''
    self.__data.clear()
