# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X                                               '
'                                                                         '
' cn5X is free software: you can redistribute it and/or modify it         '
'  under the terms of the GNU General Public License as published by      '
' the Free Software Foundation, either version 3 of the License, or       '
' (at your option) any later version.                                     '
'                                                                         '
' cn5X is distributed in the hope that it will be useful, but             '
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

class cnQPushButton(QtWidgets.QPushButton):
  '''
  QPushButton avec gestion d'images en fonction de l'état
  '''

  keyPressed       = QtCore.pyqtSignal(QtGui.QKeyEvent)
  mousePress       = QtCore.pyqtSignal(QtGui.QMouseEvent)
  mouseRelease     = QtCore.pyqtSignal(QtGui.QMouseEvent)
  mouseDoubleClick = QtCore.pyqtSignal(QtGui.QMouseEvent)

  def __init__(self, parent=None):
    super(cnQPushButton, self).__init__(parent=parent)
    self.installEventFilter(self)

    self.__mouseIsDown = False

    # Chemin des images dans le fichier de resources
    self.__imagePath = ":/cn5X/images/"
    self.__buttonStatus = False

    self.icon = QtGui.QIcon()
    self.iconDown = QtGui.QIcon()
    self.iconLight = QtGui.QIcon()
    self.__imagesOk = False

  def eventFilter(self, object, event):
    '''
    On utilise eventFilter() pour "trapper" un évennement unique au plus tôt après la création
    du contrôle car le nom n'est pas définit lors de l'appel d'__init() et je n'ai pas réussi
    à récupérer le signal objectNameChanged.
    '''
    if event.type() == QtCore.QEvent.DynamicPropertyChange:
      pictureBaseName = self.__imagePath + object.objectName()

      self.icon.addPixmap     (QtGui.QPixmap(pictureBaseName + ".svg"),       QtGui.QIcon.Normal, QtGui.QIcon.Off)
      self.iconDown.addPixmap (QtGui.QPixmap(pictureBaseName + "_down.svg"),  QtGui.QIcon.Normal, QtGui.QIcon.Off)
      self.iconLight.addPixmap(QtGui.QPixmap(pictureBaseName + "_light.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      self.__imagesOk = True

    if event.type() == QtCore.QEvent.EnabledChange:
      if self.__imagesOk:
        if self.isEnabled():
          if self.__buttonStatus:
            self.setIcon(self.iconLight)
          else:
            self.setIcon(self.icon)
        else:
          self.setIcon(self.icon)

    return False

  def mousePressEvent(self, e):
    self.__mouseIsDown = True
    super(cnQPushButton, self).mousePressEvent(e)
    self.setIcon(self.iconDown)
    self.mousePress.emit(e)

  def mouseReleaseEvent(self, e):
    self.__mouseIsDown = False
    super(cnQPushButton, self).mouseReleaseEvent(e)
    self.__buttonStatus = True
    if self.isEnabled():
      self.setIcon(self.iconLight)
    else:
      self.setIcon(self.icon)
    self.mouseRelease.emit(e)

  def setButtonStatus(self, value: bool):
    self.__buttonStatus = value
    if not self.__mouseIsDown:
      if self.isEnabled():
        if self.__buttonStatus:
          self.setIcon(self.iconLight)
        else:
          self.setIcon(self.icon)
      else:
        self.setIcon(self.icon)

  def getButtonStatus(self):
    return self.__buttonStatus

  def mouseDoubleClickEvent(self, e):
    super(cnQPushButton, self).mouseDoubleClickEvent(e)
    self.mouseDoubleClick.emit(e)

  def keyPressEvent(self, e):
    super(cnQPushButton, self).keyPressEvent(e)
    self.keyPressed.emit(e)
