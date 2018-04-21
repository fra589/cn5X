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

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets

class cnQLabel(QtWidgets.QLabel):
  '''
  QLabel avec gestion de click
  '''

  clicked     = QtCore.pyqtSignal(str, QtGui.QMouseEvent)
  doubleClick = QtCore.pyqtSignal(str, QtGui.QMouseEvent)

  def __init__(self, parent=None):
    super(cnQLabel, self).__init__(parent=parent)

  def mouseReleaseEvent(self, e):
    super(cnQLabel, self).mouseReleaseEvent(e)
    self.clicked.emit(self.text(), e)

  def mouseDoubleClickEvent(self, e):
    super(cnQLabel, self).mouseDoubleClickEvent(e)
    self.doubleClick.emit(self.text(), e)
