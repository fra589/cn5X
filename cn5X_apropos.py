# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QValidator
from cn5X_config import *
from grblCom import grblCom
from dlgAPropos import *
from msgbox import *

class cn5XAPropos(QObject):
  ''' Classe assurant la gestion de la boite de dialogue A Propos '''

  def __init__(self, versionString: str, licenceFile: str):
    super().__init__()
    self.__dlgApropos = QDialog()
    self.__di = Ui_dlgApropos()
    self.__di.setupUi(self.__dlgApropos)
    self.__di.lblVersion.setText(versionString)

    text=open(licenceFile).read()
    self.__di.qptLicence.setPlainText(text)

  def showDialog(self):
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.__dlgApropos.geometry().width()
    myHeight = self.__dlgApropos.geometry().height()
    self.__dlgApropos.setFixedSize(self.__dlgApropos.geometry().width(),self.__dlgApropos.geometry().height())
    self.__dlgApropos.move(ParentX + ((ParentWidth - myWidth) / 2),ParentY + ((ParentHeight - myHeight) / 2),)
    self.__dlgApropos.setWindowFlags(Qt.Window | Qt.Dialog)

    RC = self.__dlgApropos.exec()
    return RC

