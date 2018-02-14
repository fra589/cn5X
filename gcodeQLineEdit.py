# -*- coding: UTF-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

class gcodeQLineEdit(QtWidgets.QLineEdit):

  keyPressed = QtCore.pyqtSignal(QtGui.QKeyEvent)

  def __init__(self, parent=None):
    QtWidgets.QLineEdit.__init__(self, parent)

  def keyPressEvent(self, event):
    super(gcodeQLineEdit, self).keyPressEvent(event)
    self.keyPressed.emit(event)
