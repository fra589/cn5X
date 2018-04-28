# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X++                                               '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it         '
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

from cn5X_config import *
from grblCom import grblCom

def adjustFeedOverride(valeurDepart: int, valeurArrivee: int, grbl: grblCom):
  valeurCourante = valeurDepart
  while valeurCourante != valeurArrivee:
    if valeurCourante <= valeurArrivee - 10:
      grbl.realTimePush(REAL_TIME_FEED_PLUS_10, COM_FLAG_NO_OK)
      valeurCourante += 10
    elif valeurCourante < valeurArrivee:
      grbl.realTimePush(REAL_TIME_FEED_PLUS_1, COM_FLAG_NO_OK)
      valeurCourante += 1
    elif valeurCourante >= valeurArrivee + 10:
      grbl.realTimePush(REAL_TIME_FEED_MOINS_10, COM_FLAG_NO_OK)
      valeurCourante -= 10
    elif valeurCourante > valeurArrivee:
      grbl.realTimePush(REAL_TIME_FEED_MOINS_1, COM_FLAG_NO_OK)
      valeurCourante -= 1


def adjustSpindleOverride(valeurDepart: int, valeurArrivee: int, grbl: grblCom):
  valeurCourante = valeurDepart
  while valeurCourante != valeurArrivee:
    if valeurCourante <= valeurArrivee - 10:
      grbl.realTimePush(REAL_TIME_SPINDLE_PLUS_10, COM_FLAG_NO_OK)
      valeurCourante += 10
    elif valeurCourante < valeurArrivee:
      grbl.realTimePush(REAL_TIME_SPINDLE_PLUS_1, COM_FLAG_NO_OK)
      valeurCourante += 1
    elif valeurCourante >= valeurArrivee + 10:
      grbl.realTimePush(REAL_TIME_SPINDLE_MOINS_10, COM_FLAG_NO_OK)
      valeurCourante -= 10
    elif valeurCourante > valeurArrivee:
      grbl.realTimePush(REAL_TIME_SPINDLE_MOINS_1, COM_FLAG_NO_OK)
      valeurCourante -= 1

