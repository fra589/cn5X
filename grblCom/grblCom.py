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
from grblComSerial import grblComSerial


class logSeverity(Enum):
  info    = 0
  warning = 1
  error =   2


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
  sig_debug  = pyqtSignal(str)      # Emis à chaque envoi ou réception

  # Signaux de pilotage a envoyer au thread
  sig_abort        = pyqtSignal()
  sig_gcodeInsert  = pyqtSignal(str)
  sig_gcodePush    = pyqtSignal(str)
  sig_realTimePush = pyqtSignal(str)
  sig_clearCom     = pyqtSignal()


  def __init__(self):
    super().__init__()
    self.__threads = None
    self.__Com = None


  def startCom(self, comPort: str, baudRate: int):
    '''
    Gestion des communications série et des timers dans des threads distincts
    '''

    self.__threads = []
    self.sig_log.emit(logSeverity.info, 'grblCom: Starting grblComSerial thread.')
    self.__Com = grblComSerial(comPort, baudRate)
    thread = QThread()
    thread.setObjectName('grblComSerial')
    self.__threads.append((thread, self.__Com))  # need to store worker too otherwise will be gc'd
    self.__Com.moveToThread(thread)
    # Connecte les signaux provenant du grblComSerial
    self.__Com.sig_log.connect( ******* A SUIVRE ! *******

