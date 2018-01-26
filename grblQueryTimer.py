# -*- coding: UTF-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, QTimer, QEventLoop, pyqtSignal

class grblQueryThread(QThread):

  def __init__(self, *args, **kwargs):
    QThread.__init__(self, *args, **kwargs)
    self._Actif = False
    self.grblQueryTimer.moveToThread(self)
    self.grblQueryTimer.timeout.connect(self.grblSendQuery)

  def run(self):
    self.grblQueryTimer.start(1000)
    self._Actif = True
    loop = QEventLoop()
    loop.exec_()

  def stop(self):
    self.grblQueryTimer.stop()
    self._Actif = False

  def isActif(self):
    return self._Actif

  def grblSendQuery(self):
    print ("Sending query to Grbl")

