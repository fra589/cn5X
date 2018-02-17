# -*- coding: UTF-8 -*-

import sys, time
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

from grblCommunicator_serial import serialCommunicator

class serialTimer(QObject):

  sig_msg         = pyqtSignal(str) # Messages de fonctionnements
  sig_serialTimer = pyqtSignal(str, bool) # Signal du timer
  sig_done        = pyqtSignal()    # Emis à la fin du thread

  def __init__(self, signalPeriod: int, communicator: serialCommunicator):
    super().__init__()
    self.__sigPeriod = signalPeriod
    self.__Actif = False
    self.__loop = None
    self.__communicator = communicator

  @pyqtSlot()
  def run(self):
    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_msg.emit('serialTimer : Running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    self.__serialTimer1 = QTimer()
    self.__serialTimer1.timeout.connect(self.serialTimer1Send)
    self.__serialTimer2 = QTimer()
    self.__serialTimer2.timeout.connect(self.serialTimer2Send)
    self.__serialTimer3 = QTimer()
    self.__serialTimer3.timeout.connect(self.serialTimer3Send)
    self.__Actif = False
    self.__loop = QEventLoop()
    self.__loop.exec_()

  @pyqtSlot()
  def stop(self):
    if self.__Actif:
      self.sig_msg.emit("serialTimer : stopping timers.")
      self.__serialTimer1.stop()
      self.__serialTimer2.stop()
      self.__serialTimer3.stop()
      self.__Actif = False
    else:
      self.sig_msg.emit("serialTimer : timer not running.")

  @pyqtSlot()
  def start(self):
    if not self.__Actif:
      self.sig_msg.emit("serialTimer : starting timers.")
      sleepTime = self.__sigPeriod / 1000
      self.__serialTimer1.start(self.__sigPeriod)
      time.sleep(sleepTime / 2)
      self.__serialTimer2.start(self.__sigPeriod*4)
      time.sleep(sleepTime)
      self.__serialTimer3.start(self.__sigPeriod*4)
      self.__Actif = True
    else:
      self.sig_msg.emit("serialTimer : timers already running.")

  @pyqtSlot()
  def abort(self):
    self.sig_msg.emit("serialTimer : quit timer...")
    self.__serialTimer1.stop()
    self.__serialTimer2.stop()
    self.__serialTimer3.stop()
    self.__Actif = False
    self.__loop.quit()
    self.sig_done.emit()

  @pyqtSlot()
  def isActif(self):
    return self._Actif

  @pyqtSlot()
  def serialTimer1Send(self):
    self.sig_serialTimer.emit("?", False)

  @pyqtSlot()
  def serialTimer2Send(self):
    self.sig_serialTimer.emit("$G\n", True)

  @pyqtSlot()
  def serialTimer3Send(self):
    if self.__communicator.grblStatus() == "Idle":
      self.sig_serialTimer.emit("$#\n", True)
    else:
      #print("communicator.grblStatus = ", self.__communicator.grblStatus())
      pass
