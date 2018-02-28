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
from cn5X_config import *
from grblComSerial import grblComSerial


class grblCom(QObject):
  '''
  Gestion du thread de communication série avec Grbl
  '''

  # Reprise des signaux venant du thread de Com à faire suivre
  sig_log    = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string
  sig_init   = pyqtSignal(str)      # Emis à la réception de la chaine d'initialisation de Grbl, renvoie la chaine complète
  sig_ok     = pyqtSignal()         # Emis à la réception de la chaine "ok"
  sig_error  = pyqtSignal(int)      # Emis à la réception d'une erreur Grbl, renvoie le N° d'erreur
  sig_alarm  = pyqtSignal(int)      # Emis à la réception d'une alarme Grbl, renvoie le N° d'alarme
  sig_status = pyqtSignal(str)      # Emis à la réception d'un message de status ("<...|.>"), renvoie la ligne complète
  sig_data   = pyqtSignal(str)      # Emis à la réception des autres données de Grbl, renvoie la ligne complète
  sig_emit   = pyqtSignal(str)      # Emis à l'envoi des données sur le port série
  sig_recu   = pyqtSignal(str)      # Emis à la réception des données sur le port série
  sig_debug  = pyqtSignal(str)      # Emis à chaque envoi ou réception

  # Signaux de pilotage a envoyer au thread
  sig_abort        = pyqtSignal()
  sig_gcodeInsert  = pyqtSignal(str)
  sig_gcodePush    = pyqtSignal(str)
  sig_realTimePush = pyqtSignal(str)
  sig_clearCom     = pyqtSignal()


  def __init__(self):
    super().__init__()
    self.__threads       = None
    self.__Com           = None
    self.__connectStatus = False
    self.__grblInit      = False
    self.__grblStatus    = ""


  def startCom(self, comPort: str, baudRate: int):
    '''
    Gestion des communications série et des timers dans des threads distincts
    '''

    self.__threads = []
    self.sig_log.emit(logSeverity.info.value, 'grblCom: Starting grblComSerial thread.')
    newComSerial = grblComSerial(comPort, baudRate)
    thread = QThread()
    thread.setObjectName('grblComSerial')
    self.__threads.append((thread, newComSerial))  # need to store worker too otherwise will be gc'd
    newComSerial.moveToThread(thread)

    # Connecte les signaux provenant du grblComSerial
    newComSerial.sig_log.connect(self.sig_log.emit)
    newComSerial.sig_connect.connect(self.on_sig_connect)
    newComSerial.sig_init.connect(self.on_sig_init)
    newComSerial.sig_ok.connect(self.sig_ok.emit)
    newComSerial.sig_error.connect(self.sig_error.emit)
    newComSerial.sig_alarm.connect(self.sig_alarm.emit)
    newComSerial.sig_status.connect(self.on_sig_status)
    newComSerial.sig_data.connect(self.sig_data.emit)
    newComSerial.sig_emit.connect(self.sig_emit.emit)
    newComSerial.sig_recu.connect(self.sig_recu.emit)
    newComSerial.sig_debug.connect(self.sig_debug.emit)

    # Signaux de pilotage a envoyer au thread
    self.sig_abort.connect(newComSerial.abort)
    self.sig_gcodeInsert.connect(newComSerial.gcodeInsert)
    self.sig_gcodePush.connect(newComSerial.gcodePush)
    self.sig_realTimePush.connect(newComSerial.realTimePush)
    self.sig_clearCom.connect(newComSerial.clearCom)

    # Start the thread...
    thread.started.connect(newComSerial.run)
    thread.start()  # this will emit 'started' and start thread's event loop

    # Memorise le communicateur
    self.__Com = newComSerial


  @pyqtSlot(bool)
  def on_sig_connect(self, value: bool):
    ''' Maintien l'état de connexion '''
    self.__connectStatus = value


  @pyqtSlot(str)
  def  on_sig_init(self, buff: str):
    self.__grblInit = True
    self.sig_init.emit(buff)


  @pyqtSlot(str)
  def on_sig_status(self, buff: str):
    ''' Memorise le status de Grbl à chaque fois qu'on en voi un passer '''
    self.__grblStatus = buff[1:].split('|')[0]
    self.sig_status.emit(buff)


  def grblStatus(self):
    ''' Renvoi le dernier status Grbl vu '''
    return self.__grblStatus

  def stopCom(self):
    ''' Stop le thread des communications série '''
    self.clearCom() # Vide la file d'attente
    self.sig_log.emit(logSeverity.info.value, "Envoi signal sig_abort au thread de communications série...")
    self.sig_abort.emit()
    # Attente de la fin du (des) thread(s)
    for thread, worker in self.__threads:
        thread.quit()  # this will quit **as soon as thread event loop unblocks**
        thread.wait()  # <- so you need to wait for it to *actually* quit
    self.sig_log.emit(logSeverity.info.value, "Thread(s) enfant(s) terminé(s).")
    self.__grblInit = False


  def gcodeInsert(self, buff: str):
    if self.__connectStatus and self.__grblInit:
      self.sig_gcodeInsert.emit(buff)
    else:
      self.sig_log.emit(logSeverity.warning.value, "grblCom: Grbl non connecté ou non initialisé, [{}] impossible à envoyer".format(buff))


  def gcodePush(self, buff: str):
    if self.__connectStatus and self.__grblInit:
      self.sig_gcodePush.emit(buff)
    else:
      self.sig_log.emit(logSeverity.warning.value, "grblCom: Grbl non connecté ou non initialisé, [{}] impossible à envoyer".format(buff))


  def realTimePush(self, buff: str):
    if self.__connectStatus and self.__grblInit:
      self.sig_realTimePush.emit(buff)
    else:
      self.sig_log.emit(logSeverity.warning.value, "grblCom: Grbl non connecté ou non initialisé, [{}] impossible à envoyer".format(buff))


  def clearCom(self):
    self.sig_clearCom.emit()


  @pyqtSlot()
  def startTimer(self):
    pass


  @pyqtSlot()
  def stopTimer(self):
    pass












