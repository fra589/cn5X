# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X++                                               '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it         '
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

import sys, time
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from cn5X_config import *
from grblComSerial import grblComSerial


class grblCom(QObject):
  '''
  Gestion du thread de communication serie avec Grbl
  '''

  # Reprise des signaux venant du thread de Com a faire suivre
  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string
  sig_connect = pyqtSignal()         # Emis a la reception de la connexion
  sig_init    = pyqtSignal(str)      # Emis a la reception de la chaine d'initialisation de Grbl, renvoie la chaine complete
  sig_ok      = pyqtSignal()         # Emis a la reception de la chaine "ok"
  sig_error   = pyqtSignal(int)      # Emis a la reception d'une erreur Grbl, renvoie le N° d'erreur
  sig_alarm   = pyqtSignal(int)      # Emis a la reception d'une alarme Grbl, renvoie le N° d'alarme
  sig_status  = pyqtSignal(str)      # Emis a la reception d'un message de status ("<...|.>"), renvoie la ligne complete
  sig_config  = pyqtSignal(str)      # Emis a la reception d'une valeur de config ($XXX)
  sig_data    = pyqtSignal(str)      # Emis a la reception des autres donnees de Grbl, renvoie la ligne complete
  sig_emit    = pyqtSignal(str)      # Emis a l'envoi des donnees sur le port serie
  sig_recu    = pyqtSignal(str)      # Emis a la reception des donnees sur le port serie
  sig_debug   = pyqtSignal(str)      # Emis a chaque envoi ou reception

  # Signaux de pilotage a envoyer au thread
  sig_abort        = pyqtSignal()
  sig_gcodeInsert  = pyqtSignal(str, object)
  sig_gcodePush    = pyqtSignal(str, object)
  sig_realTimePush = pyqtSignal(str, object)
  sig_clearCom     = pyqtSignal()
  sig_startPooling = pyqtSignal()
  sig_stopPooling  = pyqtSignal()
  sig_resetSerial  = pyqtSignal(str)


  def __init__(self):
    super().__init__()
    self.decode          = None
    self.__threads       = None
    self.__Com           = None
    self.__connectStatus = False
    self.__grblInit      = False
    self.__pooling       = True
    self.__grblVersion   = ""
    self.__grblStatus    = ""
    self.__threads = []


  def setDecodeur(self, decodeur):
    self.decode = decodeur


  def startCom(self, comPort: str, baudRate: int):
    '''
    Gestion des communications serie et des timers dans des threads distincts
    '''

    # TODO : Ajout possibilité de connection réseau
    # Windows : pseudo serial over TCP driver => rien a faire
    # Linux : use socat :
    # sudo socat pty,link=/dev/ttyTCP0,raw tcp:127.0.0.1:1386
    # comPort = "ttyTCP0" (si dans /dev)
    # attention aux droits d'accès !
    # comPort = "/tmp/ttyTCP0" (chemin absolu)

    self.sig_debug.emit("grblCom.startCom(self, {}, {})".format(comPort, baudRate))

    self.sig_log.emit(logSeverity.info.value, 'grblCom: Starting grblComSerial thread on {}.'.format(comPort))
    newComSerial = grblComSerial(self.decode, comPort, baudRate, self.__pooling)
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
    newComSerial.sig_config.connect(self.sig_config.emit)
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
    self.sig_startPooling.connect(newComSerial.startPooling)
    self.sig_stopPooling.connect(newComSerial.stopPooling)
    self.sig_resetSerial.connect(newComSerial.resetSerial)

    # Start the thread...
    thread.started.connect(newComSerial.run)
    thread.start()  # this will emit 'started' and start thread's event loop

    # Memorise le communicateur
    self.__Com = newComSerial


  @pyqtSlot(bool)
  def on_sig_connect(self, value: bool):
    self.sig_debug.emit("grblCom.on_sig_connect(self, {})".format(value))
    ''' Maintien l'etat de connexion '''
    self.__connectStatus = value
    self.sig_connect.emit()


  @pyqtSlot(str)
  def  on_sig_init(self, buff: str):
    self.sig_debug.emit("grblCom.on_sig_init(self, {})".format(buff))
    self.__grblInit = True
    self.__grblVersion = buff.split("[")[0]
    self.sig_init.emit(buff)


  def grblVersion(self):
    ''' Renvoi la chaine Grbl vXXX '''
    return self.__grblVersion


  @pyqtSlot(str)
  def on_sig_status(self, buff: str):
    self.sig_debug.emit("grblCom.on_sig_status(self, {})".format(buff))
    ''' Memorise le status de Grbl a chaque fois qu'on en voi un passer '''
    self.__grblStatus = buff[1:].split('|')[0]
    self.sig_status.emit(buff)


  def grblStatus(self):
    ''' Renvoi le dernier status Grbl vu '''
    return self.__grblStatus

  def stopCom(self):
    self.sig_debug.emit("grblCom.stopCom(self)")
    ''' Stop le thread des communications serie '''
    self.clearCom() # Vide la file d'attente
    self.sig_log.emit(logSeverity.info.value, self.tr("Envoi signal sig_abort au thread de communications serie..."))
    self.sig_abort.emit()
    # Attente de la fin du (des) thread(s)
    for thread, worker in self.__threads:
        thread.quit()  # this will quit **as soon as thread event loop unblocks**
        thread.wait()  # <- so you need to wait for it to *actually* quit
    self.sig_log.emit(logSeverity.info.value, self.tr("Thread(s) enfant(s) termine(s)."))
    self.__grblInit = False
    self.__threads = []


  def gcodeInsert(self, buff: str, flag=COM_FLAG_NO_FLAG):
    if self.__connectStatus and self.__grblInit:
      self.sig_gcodeInsert.emit(buff, flag)
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl non connecte ou non initialise, [{}] impossible a envoyer").format(buff))


  def gcodePush(self, buff: str, flag=COM_FLAG_NO_FLAG):
    if self.__connectStatus and self.__grblInit:
      self.sig_gcodePush.emit(buff, flag)
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl non connecte ou non initialise, [{}] impossible a envoyer").format(buff))


  def realTimePush(self, buff: str, flag=COM_FLAG_NO_FLAG):
    if self.__connectStatus and self.__grblInit:
      self.sig_realTimePush.emit(buff, flag)
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl non connecte ou non initialise, [{}] impossible a envoyer").format(buff))


  def clearCom(self):
    self.sig_clearCom.emit()


  @pyqtSlot()
  def startPooling(self):
    self.__pooling = True
    self.sig_startPooling.emit()


  @pyqtSlot()
  def stopPooling(self):
    self.__pooling = False
    self.sig_stopPooling.emit()

  def isOpen(self):
    return self.__connectStatus


  @pyqtSlot(str)
  def resetSerial(self, buff: str):
    self.sig_resetSerial.emit(buff)
