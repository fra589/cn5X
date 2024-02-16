# -*- coding: utf-8 -*-

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

import os, sys
import threading
from PyQt6 import QtCore, QtWidgets, uic
from PyQt6.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings, QEvent, QLocale
from PyQt6.QtGui import QKeyEvent
from gcodeQLineEdit import gcodeQLineEdit
from PyQt6.QtTest import QTest

class qwKeyNum(QtWidgets.QWidget):
  ''' Widget personalise construisant le pavé numérique touch screen
  '''

  def __init__(self, parent=None):

    super().__init__()
    self.parent = parent
    
    # Initialise l'interface utilisateur du clavier
    self.keynum = QtWidgets.QFrame(parent)
    self.keynum.setStyleSheet(".QFrame{background-color: rgba(192, 192, 192, 192); border: 1px solid #000060; margin: 0px; padding: 0px;}")
    self.keynum.move(30, 48)
    self.keynum.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), "qwKeyNum_ui.ui"), self.keynum)

    self.__txt = None

    # Le clavier est masqué au départ
    self.keynum.setVisible(False)

    # Connections des evennements clavier
    self.keynum.ui.keybButton0.pressed.connect(lambda: self.keynumKey("0"))
    self.keynum.ui.keybButton1.pressed.connect(lambda: self.keynumKey("1"))
    self.keynum.ui.keybButton2.pressed.connect(lambda: self.keynumKey("2"))
    self.keynum.ui.keybButton3.pressed.connect(lambda: self.keynumKey("3"))
    self.keynum.ui.keybButton4.pressed.connect(lambda: self.keynumKey("4"))
    self.keynum.ui.keybButton5.pressed.connect(lambda: self.keynumKey("5"))
    self.keynum.ui.keybButton6.pressed.connect(lambda: self.keynumKey("6"))
    self.keynum.ui.keybButton7.pressed.connect(lambda: self.keynumKey("7"))
    self.keynum.ui.keybButton8.pressed.connect(lambda: self.keynumKey("8"))
    self.keynum.ui.keybButton9.pressed.connect(lambda: self.keynumKey("9"))
    self.keynum.ui.keybButtonMoins.pressed.connect(lambda: self.keynumKey("-"))
    self.keynum.ui.keybButtonPoint.setText(QLocale().decimalPoint())
    self.keynum.ui.keybButtonPoint.pressed.connect(lambda: self.keynumKey(QLocale().decimalPoint()))

    self.keynum.ui.keybButtonLeft.pressed.connect(lambda: self.keynumMove("Left"))
    self.keynum.ui.keybButtonRight.pressed.connect(lambda: self.keynumMove("Right"))
    self.keynum.ui.keybButtonHome.pressed.connect(lambda: self.keynumMove("Home"))
    self.keynum.ui.keybButtonEnd.pressed.connect(lambda: self.keynumMove("End"))


    self.keynum.ui.keybButtonBackSpace.pressed.connect(lambda: self.keynumDel("Back"))
    self.keynum.ui.keybButtonClear.pressed.connect(lambda: self.keynumDel("Clear"))

    self.keynum.ui.keybButtonUp.pressed.connect(lambda: self.keynumUpDown(Qt.Key.Key_Up))
    self.keynum.ui.keybButtonDown.pressed.connect(lambda: self.keynumUpDown(Qt.Key.Key_Down))

    self.keynum.ui.btnClose.pressed.connect(self.keynum_hide)

    
  @pyqtSlot(gcodeQLineEdit)
  def setLinkedTxt(self, txt):
    self.__txt = txt
    if self.__txt is not None:
      self.__txt.lineEdit().setSelection(0, len(self.__txt.lineEdit().text()))


  def keynum_show(self):
    self.keynum.setVisible(True)


  def keynum_hide(self):
    self.keynum.setVisible(False)


  def isVisible(self):
    return self.keynum.isVisible()


  def keynumKey(self, key):
    if self.__txt is not None:
      self.__txt.setFocus()
      keyEvent = QKeyEvent(QEvent.Type.KeyPress, ord(key), Qt.KeyboardModifier.NoModifier, key)
      QCoreApplication.postEvent(self.__txt, keyEvent)


  def keynumMove(self, action):
    if self.__txt is not None:
      self.__txt.setFocus()
      if action == "Left":
        if self.__txt.lineEdit().cursorPosition() > 0:
          self.__txt.lineEdit().setCursorPosition(self.__txt.lineEdit().cursorPosition()-1)
      elif action == "Right":
        if self.__txt.lineEdit().cursorPosition() < len(self.__txt.lineEdit().text()):
          self.__txt.lineEdit().setCursorPosition(self.__txt.lineEdit().cursorPosition()+1)
      elif action == "Home":
        self.__txt.lineEdit().setCursorPosition(0)
      elif action == "End":
        self.__txt.lineEdit().setCursorPosition(len(self.__txt.lineEdit().text()))


  def keynumDel(self, action):
    if self.__txt is not None:
      self.__txt.setFocus()
      if action == "Back":
        # backspace n'existe pas pour les QDoubleSpinBox 
        #self.__txt.backspace()
        keyEvent = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        QCoreApplication.postEvent(self.__txt, keyEvent)
      elif action == "Clear":
        self.__txt.clear()


  def keynumUpDown(self, key):
      keyEvent = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
      QCoreApplication.postEvent(self.__txt, keyEvent)


