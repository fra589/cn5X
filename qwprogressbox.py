# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_probe.py, is part of cn5X++                             '
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
from threading import Timer,Thread,Event
from datetime import datetime
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings
from cn5X_config import *

'''
          if gcodeLine[:1] == '(' and gcodeLine[-1:] == ")":
            self.__pBoxLblComment.setText(gcodeLine)

      total_seconds = int((datetime.now() - debut).total_seconds())
      hours, remainder = divmod(total_seconds,60*60)
      minutes, seconds = divmod(remainder,60)
      self.__pBoxLblElapse.setText(self.tr("Elapsed time: {:02d}:{:02d}:{:02d}").format(hours, minutes, seconds))

'''


class qwProgressBox(QtWidgets.QWidget):
  ''' Widget personalise construisant la boite de progression lors du streaming d'un fichier GCode
  '''

  def __init__(self, parent=None):
    super().__init__()

    self.__settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)
    
    self.pBox = QtWidgets.QFrame(parent)
    self.pBox.setStyleSheet(".QFrame{background-color: rgba(192, 192, 192, 192); border: 2px solid #000060;}")

    self.pBoxBtnHeader = btnHeader(self.pBox)
    self.pBoxBtnHeader.setStyleSheet(".btnHeader{background-color: rgba(48, 48, 80, 192); border-radius: 0px}")
    
    self.pBoxLblStart = QtWidgets.QLabel(self.pBoxBtnHeader)
    debut = datetime.now()
    self.pBoxLblStart.setText(self.tr("GCode started at: {}").format(debut.strftime("%A %x %H:%M:%S")))
    self.pBoxLblStart.setStyleSheet("color: white;")
    self.pBoxLblStart.adjustSize()
    self.pBoxBtnHeader.setGeometry(2, 2, self.pBoxLblStart.width() + 36, self.pBoxBtnHeader.height())
    self.pBoxLblStart.setGeometry(20, int((self.pBoxBtnHeader.height() - self.pBoxLblStart.height())/2), self.pBoxLblStart.width(), self.pBoxLblStart.height())

    self.pBoxProgress = QtWidgets.QProgressBar(self.pBox)
    self.pBoxProgress.setAlignment(Qt.AlignHCenter)
    self.pBoxProgress.setGeometry(20, self.pBoxBtnHeader.geometry().y()+self.pBoxBtnHeader.height()+9, self.pBoxLblStart.width(), 20)
    self.pBoxProgress.setRange(0,100)
    self.pBoxProgress.setValue(37)

    self.pBoxLblComment = QtWidgets.QLabel(self.pBox)
    self.pBoxLblComment.setText("()")
    self.pBoxLblComment.setGeometry(20, self.pBoxProgress.geometry().y()+self.pBoxProgress.height()+3, self.pBoxLblStart.width(), 20)

    self.pBoxLblElapse = QtWidgets.QLabel(self.pBox)
    total_seconds = int((datetime.now() - debut).total_seconds())
    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)
    self.pBoxLblElapse.setText(self.tr("Elapsed time:"))
    self.pBoxLblElapse.setGeometry(20, self.pBoxLblComment.geometry().y()+self.pBoxLblComment.height()+3, self.pBoxLblStart.width(), 20)

    pBoxLargeur = self.pBoxLblStart.width() + 40
    pBoxHauteur = self.pBoxLblElapse.geometry().y()+self.pBoxLblElapse.height()+6
    defaultX    = int((parent.width() - pBoxLargeur) / 2)
    defaultY    = int((parent.height() - pBoxHauteur) / 5 * 3)
    pBoxX = self.__settings.value("ProgressBox/posX", defaultX, type=int)
    pBoxY = self.__settings.value("ProgressBox/posY", defaultY, type=int)

    self.pBox.setGeometry(pBoxX, pBoxY, pBoxLargeur, pBoxHauteur)
    self.pBox.setVisible(False)
    

  def start(self):
    debut = datetime.now()
    self.pBoxLblStart.setText(self.tr("GCode started at: {}").format(debut.strftime("%A %x %H:%M:%S")))
    self.pBox.setVisible(True)
    # Démarre la mise à jour régulière du temps elapsed
    self.__elapseThread = elapseThread(self.pBoxLblElapse)
    self.__elapseThread.start()


  def stop(self):
    # Masque la boite
    self.pBox.setVisible(False)
    # Arrete la mise à jour régulière du temps elapsed
    self.__elapseThread.stop()


  def setRange(self, mini: int, maxi: int):
    self.pBoxProgress.setRange(mini, maxi)


  def setValue(self, val:int):
    self.pBoxProgress.setValue(val)
    self.pBoxProgress.setToolTip(self.tr("Line {} of {}").format(val, self.pBoxProgress.maximum()))


  def setComment(self, comment: str):
    self.pBoxLblComment.setText(comment)


  def isVisible(self):
    return self.pBox.isVisible()


class elapseThread(threading.Thread):
  
  def __init__(self, pBoxLblElapse):
    threading.Thread.__init__(self)
    self._stopevent = threading.Event()
    self.pBoxLblElapse = pBoxLblElapse
    self.initialText = pBoxLblElapse.text()


  def run(self):
    debut = datetime.now()
    while not self._stopevent.isSet():
      total_seconds = int((datetime.now() - debut).total_seconds())
      hours, remainder = divmod(total_seconds,60*60)
      minutes, seconds = divmod(remainder,60)
      self.pBoxLblElapse.setText("{} {:02d}:{:02d}:{:02d}".format(self.initialText, hours, minutes, seconds))
      self._stopevent.wait(1.0)

  def stop(self):
    self._stopevent.set()
    self.pBoxLblElapse.setText(self.initialText)


class btnHeader(QtWidgets.QPushButton):

  def __init__(self, parent=None):
    super(btnHeader, self).__init__(parent)
    self.__parent = parent
    '''self.setFlat(True)
    self.setAutoFillBackground(True)'''
    self.__settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)

  def mousePressEvent(self, e):
    self.x0 = e.x()
    self.y0 = e.y()

  def mouseMoveEvent(self, e):
    newX = self.__parent.pos().x() + (e.x() - self.x0)
    if newX < 0: newX = 0
    if newX > self.__parent.parent().width() - self.__parent.width() : newX = self.__parent.parent().width() - self.__parent.width()
    newY = self.__parent.pos().y() + (e.y() - self.y0)
    if newY < 0: newY = 0
    if newY > self.__parent.parent().height() - self.__parent.height() : newY = self.__parent.parent().height() - self.__parent.height()
    self.__parent.move(newX, newY)

  def mouseReleaseEvent(self, e):
    # Enregistre la position de la boite dans les settings
    self.__settings.setValue("ProgressBox/posX", self.__parent.pos().x())
    self.__settings.setValue("ProgressBox/posY", self.__parent.pos().y())





