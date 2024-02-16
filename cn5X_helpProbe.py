# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

import os
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QValidator
from cn5X_config import *
from msgbox import *


class cn5XHelpProbe(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue d'aide sur le probing '''

  def __init__(self, helpPage: str):
    super().__init__()
    self.setModal(False)
    self.__di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgHelpProbe.ui"), self)


    # Chargement de la page d'aide
    warning = self.tr('<p style="color: #8b0000; font-weight: bold;">Attention! Measuring operations are very intolerant of incorrect settings. It is strongly recommended to do preliminary tests on loose object that will not damage the probe when unexpected movements. It is recommended to carefully check each setting before measuring the workpiece.</p>')
    if helpPage == MENU_SINGLE_AXIS:
      content  = self.tr('<html><head/><body><h1 align="center">Probe detection of single axis.</h1>')
      content += warning
      content += self.tr('<p><i>The trajectory of the probe by the example of measurement of axis X+:</i></p>')
      content += self.tr('<p>If the "Seek rate" option is checked, the probing will be made in 2 times:<br />')
      content += self.tr('- A first probing with "Length" probing distance at "Seek rate" speed, then retract of "Pull-off dist." distance,<br />')
      content += self.tr('- A second probing with "Pull-off dist." probing distance at "Feed rate" speed.</p>')
      content += self.tr('<p align="center"><img src="' + os.path.dirname(__file__) + '/doc/probeSingleAxis.svg"/></p>')
      content += self.tr('<p>If the "Seek rate" option is unchecked, there will be only one probing with "Length" probe distance at "Feed rate" speed</p>')
      content += self.tr('<p>Due to the Grbl\'s acceleration/deceleration planning, when probing, the tool is stopped a small amount after the point. ')
      content += self.tr('When checking the "Move after probe" option, the tool will be moved either exactly on the probed point, or retracted by a "Retract" length from the result of the check.</p>')
      content += self.tr('</body></html>')
    elif helpPage == MENU_INSIDE_CORNER:
      content  = self.tr('<html><head/><body><h1 align="center">Probe detection of inside corner.</h1>')
      content += warning
      content += self.tr('<p><i>The trajectory of the probe by the example of measurement inside corner X+Y+:</i></p>')
      content += self.tr('<p align="center"><img src="' + os.path.dirname(__file__) + '/doc/probeInsideXY.svg"/></p></body></html>')
    elif helpPage == MENU_OUTSIDE_CORNER:
      content  = self.tr('<html><head/><body><h1 align="center">Probe detection of outside corner.</h1>')
      content += warning
      content += self.tr('<p><i>The trajectory of the probe by the example of measurement outside corner X+Y+:</i></p>')
      content += self.tr('<p align="center"><img src="' + os.path.dirname(__file__) + '/doc/probeOutsideXY.svg"/></p></body></html>')
    elif helpPage == MENU_INSIDE_CENTER:
      content  = self.tr('<html><head/><body><h1 align="center">Probe detection of inside center.</h1>')
      content += warning
      content += self.tr('<p align="center"><img src="' + os.path.dirname(__file__) + '/doc/probeInsideCenter.svg"/></p></body></html>')
    elif helpPage == MENU_OUTSIDE_CENTER:
      content  = self.tr('<html><head/><body><h1 align="center">Probe detection of outside center.</h1>')
      content += warning
      content += self.tr('<p align="center"><img src="' + os.path.dirname(__file__) + '/doc/probeOutsideCenter.svg"/></p></body></html>')
    self.__di.lblContent.setText(content)
    self.__di.lblContent.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    self.adjustSize()


  def showDialog(self):
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.geometry().width()
    myHeight = self.geometry().height()
    self.setFixedSize(self.geometry().width(),self.geometry().height())
    self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Tool)

    RC = self.show()
    return RC

