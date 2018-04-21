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

grblCompilOptions = {
  'V': ["Variable spindle enabled"],
  'N': ["Line numbers enabled"],
  'M': ["Mist coolant enabled"],
  'C': ["CoreXY enabled"],
  'P': ["Parking motion enabled"],
  'Z': ["Homing force origin enabled"],
  'H': ["Homing single axis enabled"],
  'T': ["Two limit switches on axis enabled"],
  'A': ["Allow feed rate overrides in probe cycles"],
  '*': ["Restore all EEPROM disabled"],
  '$': ["Restore EEPROM $ settings disabled"],
  '#': ["Restore EEPROM parameter data disabled"],
  'I': ["Build info write user string disabled"],
  'E': ["Force sync upon EEPROM write disabled"],
  'W': ["Force sync upon work coordinate offset change disabled"],
  'L': ["Homing init lock sets Grbl into an alarm state upon power up"]
}
