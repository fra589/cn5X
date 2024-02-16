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
from grblCom import grblCom
from msgbox import *


class cn5XAPropos(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue A Propos '''

  def __init__(self, versionString: str, licenceFile: str):
    super().__init__()
    self.__di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgAPropos.ui"), self)
    
    self.__di.lblVersion.setText(versionString + '\t' + "(Qt version " + QtCore.PYQT_VERSION_STR + ")")

    text=open(licenceFile).read()
    self.__di.qptLicence.setPlainText(text)

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
    self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.Dialog)

    RC = self.exec()
    return RC

