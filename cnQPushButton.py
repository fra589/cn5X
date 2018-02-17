# -*- coding: UTF-8 -*-

import sys, os
from PyQt5 import QtCore, QtGui, QtWidgets
from pathlib import Path

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

    # Chemin des images
    appPath = os.path.abspath(os.path.dirname(sys.argv[0]))
    self.__imagePath = appPath + "/images/"
    self.__buttonStatus = False

    self.icon = QtGui.QIcon()
    self.iconDown = QtGui.QIcon()
    self.iconLight = QtGui.QIcon()

  def eventFilter(self, object, event):
    if event.type() == QtCore.QEvent.DynamicPropertyChange:
      pictureBaseName = self.__imagePath + object.objectName()

      f = Path(pictureBaseName + ".svg")
      if f.is_file():
        self.icon.addPixmap(QtGui.QPixmap(pictureBaseName + ".svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      else:
        print ("Image du bouton {} non trouvée.".format(pictureBaseName + ".svg"))

      f = Path(pictureBaseName + "_down.svg")
      if f.is_file():
        self.iconDown.addPixmap(QtGui.QPixmap(pictureBaseName + "_down.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      else:
        print ("Image du bouton {} non trouvée.".format(pictureBaseName + "_down.svg"))

      f = Path(pictureBaseName + "_light.svg")
      if f.is_file():
        self.iconLight.addPixmap(QtGui.QPixmap(pictureBaseName + "_light.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      else:
        print ("Image du bouton {} non trouvée.".format(pictureBaseName + "_light.svg"))

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
    if self.__buttonStatus:
      self.setIcon(self.iconLight)
    else:
      self.setIcon(self.icon)
    self.mouseRelease.emit(e)

  def setButtonStatus(self, value: bool):
    self.__buttonStatus = value
    if not self.__mouseIsDown:
      if self.__buttonStatus:
        self.setIcon(self.iconLight)
      else:
        self.setIcon(self.icon)

  def getButtonStatus(self):
    return self.__buttonStatus

  def mouseDoubleClickEvent(self, e):
    print("mouseDoubleClickEvent")
    super(cnQPushButton, self).mouseDoubleClickEvent(e)
    self.mouseDoubleClick.emit(e)

  def keyPressEvent(self, e):
    super(cnQPushButton, self).keyPressEvent(e)
    self.keyPressed.emit(e)
