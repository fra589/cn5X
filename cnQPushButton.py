# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2021 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets

class cnQPushButton(QtWidgets.QPushButton):
  '''
  QPushButton avec gestion d'images en fonction de l'etat
  '''

  keyPressed       = QtCore.pyqtSignal(QtGui.QKeyEvent)
  mousePress       = QtCore.pyqtSignal(QtWidgets.QPushButton, QtGui.QMouseEvent)
  mouseRelease     = QtCore.pyqtSignal(QtWidgets.QPushButton, QtGui.QMouseEvent)
  mouseDoubleClick = QtCore.pyqtSignal(QtGui.QMouseEvent)

  def __init__(self, parent=None):
    super(cnQPushButton, self).__init__(parent=parent)
    self.installEventFilter(self)
    self.__myName = ""
    self.__mouseIsDown = False
    self.__buttonStatus = False

    # Chemin des images dans le fichier de resources
    self.__imagePath = ":/cn5X/images/"

    self.icon = QtGui.QIcon()
    self.iconDown = QtGui.QIcon()
    self.iconLight = QtGui.QIcon()
    self.__imagesOk = False

  def eventFilter(self, object, event):
    '''
    On utilise eventFilter() pour "trapper" un evennement unique au plus tot apres la creation
    du controle car le nom n'est pas definit lors de l'appel d'__init() et je n'ai pas reussi
    a recuperer le signal objectNameChanged.
    '''
    if event.type() == QtCore.QEvent.DynamicPropertyChange:
      self.__myName = object.objectName()
      pictureBaseName = self.__imagePath + self.__myName.split("_")[0]

      if QtCore.QResource(pictureBaseName + ".svg").isValid():
        self.icon.addPixmap     (QtGui.QPixmap(pictureBaseName + ".svg"),       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        if QtCore.QResource(pictureBaseName + "_down.svg").isValid():
          self.iconDown.addPixmap (QtGui.QPixmap(pictureBaseName + "_down.svg"),  QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
          self.iconDown.addPixmap (QtGui.QPixmap(pictureBaseName + ".svg"),  QtGui.QIcon.Normal, QtGui.QIcon.Off)
        if QtCore.QResource(pictureBaseName + "_light.svg").isValid():
          self.iconLight.addPixmap(QtGui.QPixmap(pictureBaseName + "_light.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        else:
          self.iconLight.addPixmap (QtGui.QPixmap(pictureBaseName + ".svg"),  QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.__imagesOk = True
      else:
        #print(self.tr("Image resource of button ({}) not found").format(pictureBaseName + ".svg"))
        pass

    if event.type() == QtCore.QEvent.EnabledChange:
      if self.__imagesOk:
        if self.isEnabled():
          if self.__buttonStatus:
            self.setIcon(self.iconLight)
          else:
            self.setIcon(self.icon)
        else:
          self.setIcon(self.icon)

    if event.type() == QtCore.QEvent.Resize:
      self.setIconSize(QtCore.QSize(self.size().width()-2, self.size().height()-2))
    
    return False


  def changeIcon(self, icon):
    newIcon = QtGui.QIcon()
    newIcon.addPixmap(QtGui.QPixmap(icon), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    self.setIcon(newIcon)


  def mousePressEvent(self, e):
    super(cnQPushButton, self).mousePressEvent(e)
    if e.button() == QtCore.Qt.LeftButton:
      self.__mouseIsDown = True
      if self.__imagesOk:
        self.setIcon(self.iconDown)
      self.mousePress.emit(self, e)

  def mouseReleaseEvent(self, e):
    super(cnQPushButton, self).mouseReleaseEvent(e)
    if e.button() == QtCore.Qt.LeftButton:
      self.__mouseIsDown = False
      if self.isCheckable():
        self.__buttonStatus = True
      if self.__imagesOk:
        if self.isEnabled():
          if self.__buttonStatus:
            self.setIcon(self.iconLight)
          else:
            self.setIcon(self.icon)
        else:
          self.setIcon(self.icon)
      self.mouseRelease.emit(self, e)

  def setButtonStatus(self, value: bool):
    self.__buttonStatus = value
    if not self.__mouseIsDown:
      if self.__imagesOk:
        if self.isEnabled():
          if self.__buttonStatus:
            self.setIcon(self.iconLight)
          else:
            self.setIcon(self.icon)
        else:
          self.setIcon(self.icon)

  def isMouseDown(self):
    return self.__mouseIsDown

  def getButtonStatus(self):
    return self.__buttonStatus

  def name(self):
    return self.__myName

  def mouseDoubleClickEvent(self, e):
    super(cnQPushButton, self).mouseDoubleClickEvent(e)
    self.mouseDoubleClick.emit(e)

  def keyPressEvent(self, e):
    super(cnQPushButton, self).keyPressEvent(e)
    self.keyPressed.emit(e)
