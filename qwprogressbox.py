# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

import sys, os
import threading
from threading import Timer,Thread,Event
from datetime import datetime
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings, QSize
from cn5X_config import *
from grblDecode import grblDecode


class qwProgressBox(QtWidgets.QWidget):
  ''' Widget personalise construisant la boite de progression lors du streaming d'un fichier GCode
  '''

  def __init__(self, parent=None):
    super().__init__()

    self.__decode    = None
    self.__settings  = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)
    self.__autoClose = self.__settings.value("ProgressBox/autoClose", False, type=bool)

    pBoxLargeur = 370
    pBoxHauteur = 50
    
    self.pBox = QtWidgets.QFrame(parent)
    self.pBox.setStyleSheet(".QFrame{background-color: rgba(192, 192, 192, 192); border: 2px solid #000060; margin: 0px; padding: 0px;}")
    self.pBox.resize(pBoxLargeur, 155)

    self.verticalLayout = QtWidgets.QVBoxLayout(self.pBox)
    self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetFixedSize)
    self.verticalLayout.setContentsMargins(0, 0, 0, 0)
    self.verticalLayout.setSpacing(0)
    self.verticalLayout.setObjectName("verticalLayout")

    self.pBoxBtnHeader = btnHeader(self.pBox)
    self.pBoxBtnHeader.setStyleSheet(".btnHeader{color: white; background-color: rgba(48, 48, 80, 192); border-radius: 0px; padding-top: 3px; padding-bottom: 3px;}")
    debut = datetime.now()
    self.pBoxBtnHeader.setText(self.tr("GCode started at: {}").format(debut.strftime("%A %x %H:%M:%S")))
    self.verticalLayout.addWidget(self.pBoxBtnHeader)

    self.gridLayout = QtWidgets.QGridLayout()
    self.gridLayout.setContentsMargins(10, 10, 10, 5)
    self.gridLayout.setHorizontalSpacing(3)
    self.gridLayout.setVerticalSpacing(2)
    self.gridLayout.setObjectName("gridLayout")

    self.pBoxProgress = QtWidgets.QProgressBar(self.pBox)
    self.pBoxProgress.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    self.pBoxProgress.setRange(0,100)
    self.pBoxProgress.setValue(0)
    self.pBoxProgress.setFormat("line %v of %m (%p%)")
    self.gridLayout.addWidget(self.pBoxProgress, 1, 0, 1, 2)

    self.pBoxLblComment = QtWidgets.QLabel(self.pBox)
    self.pBoxLblComment.setText("")
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.pBoxLblComment.sizePolicy().hasHeightForWidth())
    self.pBoxLblComment.setSizePolicy(sizePolicy)
    self.pBoxLblComment.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.gridLayout.addWidget(self.pBoxLblComment, 2, 0, 1, 2)
    
    self.pBoxLblElapse = QtWidgets.QLabel(self.pBox)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.pBoxLblElapse.sizePolicy().hasHeightForWidth())
    self.pBoxLblElapse.setSizePolicy(sizePolicy)
    self.pBoxLblElapse.setObjectName("pBoxLblElapse")
    total_seconds = int((datetime.now() - debut).total_seconds())
    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)
    self.__initialText = self.tr("Elapsed time:")
    self.pBoxLblElapse.setText("{} {:02d}:{:02d}:{:02d}".format(self.__initialText, hours, minutes, seconds))
    self.gridLayout.addWidget(self.pBoxLblElapse, 3, 0, 1, 1)

    self.pBoxBtnClose = QtWidgets.QPushButton(self.tr("Close"), self.pBox)
    font = QtGui.QFont()
    font.setPointSize(10)
    self.pBoxBtnClose.setFont(font)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "images/btnClose.svg")), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.On)
    self.pBoxBtnClose.setIcon(icon)
    self.pBoxBtnClose.setIconSize(QSize(12, 12))
    self.pBoxBtnClose.setObjectName("pBoxBtnClose")
    self.pBoxBtnClose.setEnabled(False)
    self.gridLayout.addWidget(self.pBoxBtnClose, 3, 1, 1, 1)

    self.pBoxBtnClose.clicked.connect(self.stop)

    self.pBoxChkAutoClose = QtWidgets.QCheckBox(self.pBox)
    self.pBoxChkAutoClose.setText(self.tr("Auto close"))
    self.pBoxChkAutoClose.setChecked(self.__autoClose)
    self.pBoxChkAutoClose.setObjectName("pBoxChkAutoClose")
    self.gridLayout.addWidget(self.pBoxChkAutoClose, 4, 1, 1, 1)

    self.pBoxChkAutoClose.clicked.connect(self.on_pBoxChkAutoClose)

    self.verticalLayout.addLayout(self.gridLayout)

    defaultX    = int((parent.width() - pBoxLargeur) / 2)
    defaultY    = int((parent.height() - pBoxHauteur) / 5 * 3)
    pBoxX = self.__settings.value("ProgressBox/posX", defaultX, type=int)
    pBoxY = self.__settings.value("ProgressBox/posY", defaultY, type=int)
    self.pBox.move(pBoxX, pBoxY)

    self.pBox.setVisible(False)


  def setDecoder(self, decoder: grblDecode):
    self.__decode = decoder


  def on_pBoxChkAutoClose(self):
    self.__autoClose = self.pBoxChkAutoClose.isChecked()
    # Enregistre le choix les settings
    self.__settings.setValue("ProgressBox/autoClose", self.__autoClose)


  def autoClose(self):
    return self.__autoClose


  def start(self):
    debut = datetime.now()
    self.pBoxLblComment.setText("")
    self.pBoxBtnHeader.setText(self.tr("GCode started at: {}").format(debut.strftime("%A %x %H:%M:%S")))
    self.pBoxBtnClose.setEnabled(False)
    self.pBox.setVisible(True)
    # Démarre la mise à jour régulière du temps elapsed
    self.__elapseThread = elapseThread(self.pBoxLblElapse, self.__decode, self.__initialText)
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
    self.pBoxProgress.update()
    QCoreApplication.processEvents()


  def setComment(self, comment: str):
    self.pBoxLblComment.setText(comment)


  def isVisible(self):
    return self.pBox.isVisible()


  def enableClose(self):
    self.pBoxBtnClose.setEnabled(True)


class elapseThread(threading.Thread):
  
  def __init__(self, label, decoder, initialText):
    threading.Thread.__init__(self)
    self.__stopevent     = threading.Event()
    self.__pBoxLblElapse = label
    self.__initialText   = initialText
    self.__decode        = decoder


  def run(self):
    total_seconds = 0
    debut      = datetime.now()
    lastElapse = debut
    while not self.__stopevent.isSet():
      maintenant = datetime.now()
      if (self.__decode is not None) and (self.__decode.get_etatMachine() == GRBL_STATUS_RUN):
        total_seconds += int((maintenant - lastElapse).total_seconds())
        hours, remainder = divmod(total_seconds,60*60)
        minutes, seconds = divmod(remainder,60)
        self.__pBoxLblElapse.setText("{} {:02d}:{:02d}:{:02d}".format(self.__initialText, hours, minutes, seconds))
      lastElapse = maintenant
      self.__stopevent.wait(1.0)

  def stop(self):
    self.__stopevent.set()
    self.__pBoxLblElapse.setText(self.__initialText)


class btnHeader(QtWidgets.QPushButton):

  def __init__(self, parent=None):
    super(btnHeader, self).__init__(parent)
    self.__parent = parent
    '''self.setFlat(True)
    self.setAutoFillBackground(True)'''
    self.__settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)

  def mousePressEvent(self, e):
    self.x0 = e.position().x()
    self.y0 = e.position().y()

  def mouseMoveEvent(self, e):
    newX = self.__parent.pos().x() + (e.position().x() - self.x0)
    if newX < 0: newX = 0
    if newX > self.__parent.parent().width() - self.__parent.width() : newX = self.__parent.parent().width() - self.__parent.width()
    newY = self.__parent.pos().y() + (e.position().y() - self.y0)
    if newY < 0: newY = 0
    if newY > self.__parent.parent().height() - self.__parent.height() : newY = self.__parent.parent().height() - self.__parent.height()
    self.__parent.move(int(newX), int(newY))

  def mouseReleaseEvent(self, e):
    # Enregistre la position de la boite dans les settings
    self.__settings.setValue("ProgressBox/posX", self.__parent.pos().x())
    self.__settings.setValue("ProgressBox/posY", self.__parent.pos().y())





