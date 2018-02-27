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

import sys, time
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

from grblCommunicator_serial import serialCommunicator
from grblCommunicator_stack import grblSerialStack
from grblCommunicator_timer import serialTimer

class grblCommunicator(QObject):
  """
  Objet servant à la communication avec grbl
  2 sous classes sont utilisées :
  - serialCommunicator : pour la lecture et l'écriture depuis et vers le port série,
  - serialTimer : timer qui intéroge grbl (?) à interval régulier pour tenir à jour la position et l'état du grbl,
  chacune de ces 2 classes vivant dans son propre thread.
  """

  # Définition des signaux externes
  sig_msg          = pyqtSignal(str)
  sig_init         = pyqtSignal(str) # Emis à la réception de la chaine d'initialisation de Grbl
  sig_grblOk       = pyqtSignal()    # Grbl Responses "ok"
  sig_grblError    = pyqtSignal()    # Grbl Erreur
  sig_grblAlarm    = pyqtSignal()    # Grbl Alarme
  sig_grblResponse = pyqtSignal(str) # Grbl Responses "error:X" ou "ALARM:X"
  sig_grblStatus   = pyqtSignal(str) # < > : Enclosed chevrons contains status report data.
  sig_data_recived = pyqtSignal(str) # Other Push Messages from Grbl
  sig_data_debug   = pyqtSignal(str) # All data from Grbl


  # Définition des signaux internes
  sig_abort_serial = pyqtSignal()
  sig_serial_send  = pyqtSignal(str, bool)
  sig_abort_timer  = pyqtSignal()
  sig_start_timer  = pyqtSignal()
  sig_stop_timer   = pyqtSignal()

  def __init__(self):
    super().__init__()
    self.__threads = None
    self.__timer1Delay = 80 # Millisecondes
    self.__Com = None
    self.__timeOutEnQueue = 60 # Timeout sur l'envoi d'une nouvelle ligne si Grbl n'a pas répondu OK en 1 minute.
    self.__serialStack = grblSerialStack()

  def startCommunicator(self, comPort: str, baudRate: int):
    '''
    Gestion des communications série et des timers dans des threads distincts
    '''
    self.__threads = []
    # Lance le serialCommunicator dans un thread distinct
    self.sig_msg.emit('grblCommunicator: Starting serialCommunicator thread.')
    communicator = serialCommunicator(comPort, baudRate, self.__serialStack)
    thread = QThread()
    thread.setObjectName('serialCommunicator')
    self.__threads.append((thread, communicator))  # need to store worker too otherwise will be gc'd
    communicator.moveToThread(thread)
    # Connecte les signaux du communicator
    communicator.sig_msg.connect(self.sig_msg.emit)               # Message de fonctionnements du communicator
    communicator.sig_init.connect(self.on_sig_init)               # Message d'initialisation de Grbl transmis
    communicator.sig_ok.connect(self.on_ok)                       # Reponses Grbl "ok"
    communicator.sig_error.connect(self.on_error)                 # Erreur Grbl
    communicator.sig_alarm.connect(self.on_alarm)                 # Alarme Grbl
    communicator.sig_response.connect(self.sig_grblResponse.emit) # Reponses Grbl "error:X" ou "ALARM:X" transmises
    communicator.sig_status.connect(self.sig_grblStatus.emit)     # Transmission Status Grbl
    communicator.sig_data.connect(self.sig_data_recived.emit)     # Autres données reçues de Grbl
    communicator.sig_data_debug.connect(self.sig_data_debug.emit)
    communicator.sig_done.connect(self.on_communicator_close)     # Emis à la fin du thread du communicator
    communicator.sig_send_ok.connect(self.on_send_ok)             # Données envoyées
    # control du communicator :
    self.sig_serial_send.connect(communicator.sendData)
    self.sig_abort_serial.connect(communicator.abort)
    # Start the thread...
    thread.started.connect(communicator.run)
    thread.start()  # this will emit 'started' and start thread's event loop
    self.__Com = communicator

    # Lance le serialTimer dans un thread distinct
    self.sig_msg.emit('grblCommunicator: Starting serialTimer thread.')
    timer1 = serialTimer(self.__timer1Delay, communicator)
    thread = QThread()
    thread.setObjectName('serialTimer1')
    self.__threads.append((thread, timer1))  # need to store worker too otherwise will be gc'd
    timer1.moveToThread(thread)
    # Connecte les signaux du timer1
    timer1.sig_msg.connect(self.sig_msg.emit)             # Message de fonctionnements du timer1
    timer1.sig_serialTimer.connect(communicator.sendData) # Passe le top timer au communicator pour envoi sur le port serie
    timer1.sig_done.connect(self.on_timer1_close)         # Emis à la fin du thread du timer1
    # control du timer1
    communicator.sig_grbl_ok.connect(timer1.start)
    self.sig_start_timer.connect(timer1.start)
    self.sig_stop_timer.connect(timer1.stop)
    self.sig_abort_timer.connect(timer1.abort)
    # Start the thread...
    thread.started.connect(timer1.run)
    thread.start()

  def startTimer(self):
    self.sig_start_timer.emit()

  def stopTimer(self):
    self.sig_stop_timer.emit()

  def stopCommunicator(self):
    self.sig_msg.emit("Envoi signal sig_abort_timer...")
    self.sig_stop_timer.emit()
    self.sig_abort_timer.emit()
    self.sig_msg.emit("Envoi signal sig_abort_serial...")
    self.sig_abort_serial.emit()
    # Attente de la fin des threads
    for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
        thread.quit()  # this will quit **as soon as thread event loop unblocks**
        thread.wait()  # <- so you need to wait for it to *actually* quit
    self.sig_msg.emit("Thread(s) enfant(s) terminé(s).")

  @pyqtSlot()
  def on_communicator_close(self):
    self.sig_msg.emit('grblCommunicator: serialCommunicator closed.')

  @pyqtSlot()
  def on_send_ok(self):
    pass

  @pyqtSlot()
  def on_timer1_close(self):
    self.sig_msg.emit('grblCommunicator: serialTimer closed.')

  @pyqtSlot(str)
  def on_sig_init(self, buff: str):
    self.sig_init.emit(buff)

  @pyqtSlot()
  def on_ok(self):
    self.sig_grblOk.emit()

  @pyqtSlot()
  def on_error(self):
    self.sig_grblError.emit()

  @pyqtSlot()
  def on_alarm(self):
    self.sig_grblAlarm.emit()

  @pyqtSlot(str)
  def addFiFo(self, buff: str):
    self.__serialStack.addFiFo(buff)

  @pyqtSlot(str)
  def addLiFo(self, buff: str):
    self.__serialStack.addLiFo(buff)

  @pyqtSlot()
  def clearStack(self):
    self.__serialStack.clear()

  @pyqtSlot()
  def stackEmpty(self):
    return self.__serialStack.isEmpty()

  @pyqtSlot()
  def grblStatus(self):
    return self.__Com.grblStatus()

  @pyqtSlot(str, bool)
  def sendData(self, buff: str, trapOk: bool = False):
    '''
    Ne doit être utilisé que par les timers ou par les commandes temps réel
    qui ne génèrent pas de message OK de la part de Grbl.
    '''
    print("Emission signal sig_serial_send()")
    self.sig_serial_send.emit(buff, trapOk)
