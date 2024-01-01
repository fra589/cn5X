# -*- coding: utf-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

import sys
import threading
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings, QEvent
from PyQt5.QtGui import QKeyEvent
from gcodeQLineEdit import gcodeQLineEdit
from PyQt5.QtTest import QTest

import qwKeyboard_ui

class qwKeyboard(QtWidgets.QWidget):
  ''' Widget personalise construisant le clavier touch screen
  '''

  def __init__(self, parent=None):
    super().__init__()
    
    self.__txt = None

    # Initialise l'interface utilisateur du clavier
    self.parent = parent
    self.keyboard = QtWidgets.QFrame(parent)
    self.keyboard.setStyleSheet(".QFrame{background-color: rgba(192, 192, 192, 192); border: 1px solid #000060; margin: 0px; padding: 0px;}")
    self.keyboard.move(5, 265)
    self.keyboard.ui = qwKeyboard_ui.Ui_keyboard()
    self.keyboard.ui.setupUi(self.keyboard)
    # Le clavier est masqué au départ
    self.keyboard.setVisible(False)

    # Connections des evennements clavier
    self.keyboard.ui.keybButtonHideL.pressed.connect(self.keyboard_hide)    
    self.keyboard.ui.keybButtonHideR.pressed.connect(self.keyboard_hide)    

    self.keyboard.ui.keybButton0.pressed.connect(lambda: self.keyboardKey("0"))
    self.keyboard.ui.keybButton1.pressed.connect(lambda: self.keyboardKey("1"))
    self.keyboard.ui.keybButton2.pressed.connect(lambda: self.keyboardKey("2"))
    self.keyboard.ui.keybButton3.pressed.connect(lambda: self.keyboardKey("3"))
    self.keyboard.ui.keybButton4.pressed.connect(lambda: self.keyboardKey("4"))
    self.keyboard.ui.keybButton5.pressed.connect(lambda: self.keyboardKey("5"))
    self.keyboard.ui.keybButton6.pressed.connect(lambda: self.keyboardKey("6"))
    self.keyboard.ui.keybButton7.pressed.connect(lambda: self.keyboardKey("7"))
    self.keyboard.ui.keybButton8.pressed.connect(lambda: self.keyboardKey("8"))
    self.keyboard.ui.keybButton9.pressed.connect(lambda: self.keyboardKey("9"))
    self.keyboard.ui.keybButtonMoins.pressed.connect(lambda: self.keyboardKey("-"))
    self.keyboard.ui.keybButtonPoint.pressed.connect(lambda: self.keyboardKey("."))

    self.keyboard.ui.keybButtonA.pressed.connect(lambda: self.keyboardKey("A"))
    self.keyboard.ui.keybButtonB.pressed.connect(lambda: self.keyboardKey("B"))
    self.keyboard.ui.keybButtonC.pressed.connect(lambda: self.keyboardKey("C"))
    self.keyboard.ui.keybButtonD.pressed.connect(lambda: self.keyboardKey("D"))
    self.keyboard.ui.keybButtonE.pressed.connect(lambda: self.keyboardKey("E"))
    self.keyboard.ui.keybButtonF.pressed.connect(lambda: self.keyboardKey("F"))
    self.keyboard.ui.keybButtonG.pressed.connect(lambda: self.keyboardKey("G"))
    self.keyboard.ui.keybButtonH.pressed.connect(lambda: self.keyboardKey("H"))
    self.keyboard.ui.keybButtonI.pressed.connect(lambda: self.keyboardKey("I"))
    self.keyboard.ui.keybButtonJ.pressed.connect(lambda: self.keyboardKey("J"))
    self.keyboard.ui.keybButtonK.pressed.connect(lambda: self.keyboardKey("K"))
    self.keyboard.ui.keybButtonL.pressed.connect(lambda: self.keyboardKey("L"))
    self.keyboard.ui.keybButtonM.pressed.connect(lambda: self.keyboardKey("M"))
    self.keyboard.ui.keybButtonN.pressed.connect(lambda: self.keyboardKey("N"))
    self.keyboard.ui.keybButtonO.pressed.connect(lambda: self.keyboardKey("O"))
    self.keyboard.ui.keybButtonP.pressed.connect(lambda: self.keyboardKey("P"))
    self.keyboard.ui.keybButtonQ.pressed.connect(lambda: self.keyboardKey("Q"))
    self.keyboard.ui.keybButtonR.pressed.connect(lambda: self.keyboardKey("R"))
    self.keyboard.ui.keybButtonS.pressed.connect(lambda: self.keyboardKey("S"))
    self.keyboard.ui.keybButtonT.pressed.connect(lambda: self.keyboardKey("T"))
    self.keyboard.ui.keybButtonU.pressed.connect(lambda: self.keyboardKey("U"))
    self.keyboard.ui.keybButtonV.pressed.connect(lambda: self.keyboardKey("V"))
    self.keyboard.ui.keybButtonW.pressed.connect(lambda: self.keyboardKey("W"))
    self.keyboard.ui.keybButtonX.pressed.connect(lambda: self.keyboardKey("X"))
    self.keyboard.ui.keybButtonY.pressed.connect(lambda: self.keyboardKey("Y"))
    self.keyboard.ui.keybButtonZ.pressed.connect(lambda: self.keyboardKey("Z"))

    self.keyboard.ui.keybButtonSpace.pressed.connect(lambda: self.keyboardKey(" "))
    self.keyboard.ui.keybButtonEgal.pressed.connect(lambda: self.keyboardKey("="))
    self.keyboard.ui.keybButtonDollar.pressed.connect(lambda: self.keyboardKey("$"))
    self.keyboard.ui.keybButtonSharp.pressed.connect(lambda: self.keyboardKey("#"))

    self.keyboard.ui.keybButtonQuestion.pressed.connect(lambda: self.keyboardKey("?"))

    self.keyboard.ui.keybButtonHome.pressed.connect(lambda: self.keyboardMove("Home"))
    self.keyboard.ui.keybButtonLeft.pressed.connect(lambda: self.keyboardMove("Left"))
    self.keyboard.ui.keybButtonRight.pressed.connect(lambda: self.keyboardMove("Right"))
    self.keyboard.ui.keybButtonEnd.pressed.connect(lambda: self.keyboardMove("End"))

    self.keyboard.ui.keybButtonBackSpace.pressed.connect(lambda: self.keyboardDel("Back"))
    self.keyboard.ui.keybButtonClear.pressed.connect(lambda: self.keyboardDel("Clear"))

    self.keyboard.ui.keybButtonUp.pressed.connect(lambda: self.keyboardUpDown(Qt.Key_Up))
    self.keyboard.ui.keybButtonDown.pressed.connect(lambda: self.keyboardUpDown(Qt.Key_Down))

  @pyqtSlot(gcodeQLineEdit)
  def setLinkedTxt(self, txt):
    self.__txt = txt


  def keyboard_show(self):
    self.keyboard.setVisible(True)


  def keyboard_hide(self):
    self.keyboard.setVisible(False)


  def isVisible(self):
    return self.keyboard.isVisible()


  def keyboardKey(self, key):
    if self.__txt is not None:
      self.__txt.setFocus()
      keyEvent = QKeyEvent(QEvent.KeyPress, ord(key), Qt.NoModifier, key)
      QCoreApplication.postEvent(self.__txt, keyEvent)


  def keyboardMove(self, action):
    if self.__txt is not None:
      self.__txt.setFocus()
      if action == "Home":
        self.__txt.setCursorPosition(0)
      elif action == "Left":
        if self.__txt.cursorPosition() > 0:
          self.__txt.setCursorPosition(self.__txt.cursorPosition()-1)
      elif action == "Right":
        if self.__txt.cursorPosition() < len(self.__txt.text()):
          self.__txt.setCursorPosition(self.__txt.cursorPosition()+1)
      elif action == "End":
        self.__txt.setCursorPosition(len(self.__txt.text()))


  def keyboardDel(self, action):
    if self.__txt is not None:
      self.__txt.setFocus()
      if action == "Back":
        self.__txt.backspace()
      elif action == "Clear":
        self.__txt.clear()


  def keyboardUpDown(self, QtKey):
    if self.__txt is not None:
      self.__txt.setFocus()
      keyEvent = QKeyEvent(QEvent.KeyPress, QtKey, Qt.NoModifier)
      QCoreApplication.postEvent(self.__txt, keyEvent)
    
    
