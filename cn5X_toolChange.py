# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_toolChange.py, is part of cn5X++                        '
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

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QSettings
from PyQt5.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit
from PyQt5.QtGui import QPalette
from cn5X_config import *
from grblCom import grblCom
from dlgToolChange import *

class dlgToolChange(QObject):
  ''' Classe assurant la gestion de la boite de dialogue changement d'outils '''

  sig_close = pyqtSignal()         # Emis a la fermeture de la boite de dialogue


  def __init__(self, grbl: grblCom, decoder, axisNumber: int, axisNames: list, toolNum: int = 0):
    super().__init__()
    self.__dlg = QDialog()
    self.di = Ui_dlgToolChange()
    self.di.setupUi(self.__dlg)

    self.__dlg.finished.connect(self.sig_close.emit)
    self.di.btnGo.clicked.connect(self.on_btnGo)    
    self.di.btnStop.clicked.connect(self.on_btnStop)    

    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames

    self.di.lblMessage.setText(self.tr("Insert tool number {}\nand click the 'Go' button\nto continue when ready.".format(toolNum)))


  def showDialog(self):
    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.__dlg.geometry().width()
    myHeight = self.__dlg.geometry().height()
    self.__dlg.setFixedSize(self.__dlg.geometry().width(),self.__dlg.geometry().height())
    self.__dlg.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.__dlg.setWindowFlags(Qt.Dialog | Qt.Tool | Qt.WindowStaysOnTopHint)
    
    RC = self.__dlg.exec() # Use exec to make the dialog application modal.
    return RC


  def on_btnGo(self):
    self.__dlg.accept()


  def on_btnStop(self):
    self.__dlg.reject()








