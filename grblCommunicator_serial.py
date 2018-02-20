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

class serialCommunicator(QObject):
  """
  Worker must derive from QObject in order to emit signals,
  connect slots to other signals, and operate in a QThread.
  """
  sig_msg        = pyqtSignal(str) # Messages de fonctionnements
  sig_init       = pyqtSignal(str) # Emis à la réception de la chaine d'initialisation de Grbl
  sig_grbl_ok    = pyqtSignal()    # Emis quand Grbl à fini son initialisation
  sig_ok         = pyqtSignal()    # Reponses "ok"
  sig_response   = pyqtSignal(str) # Reponses "error:X" ou "ALARM:X"
  sig_error      = pyqtSignal()    # Error trap
  sig_alarm      = pyqtSignal()    # Alarm trap
  sig_status     = pyqtSignal(str) # Status "<***>"
  sig_data       = pyqtSignal(str) # Emis à chaque autre ligne de données reçue
  sig_data_debug = pyqtSignal(str) # All data from Grbl
  sig_send_ok    = pyqtSignal()    # Emis à chaque ligne envoyée
  sig_done       = pyqtSignal()    # Emis à la fin du thread

  def __init__(self, comPort: str, baudRate: int):
    super().__init__()
    self.__abort      = False
    self.__portName   = comPort
    self.__baudRate   = baudRate
    self.__okToSend   = False
    self.__grblStatus = ""
    self.__okTrap     = 0

  @pyqtSlot()
  def run(self):
    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_msg.emit('Running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    # Configuration du port série
    self.__comPort = QSerialPort()
    self.__comPort.setPortName(self.__portName)
    self.__comPort.setBaudRate(self.__baudRate)
    self.__comPort.setDataBits(QSerialPort.Data8)
    self.__comPort.setStopBits(QSerialPort.OneStop)
    self.__comPort.setParity(QSerialPort.NoParity)

    # Ouverture du port série
    RC = False
    try:
      RC = self.__comPort.open(QIODevice.ReadWrite)
    except OSError as err:
      self.sig_msg.emit("serialCommunicator : Erreur ouverture du port : {0}".format(err))
    except:
      self.sig_msg.emit("serialCommunicator : Unexpected error : {}".format(sys.exc_info()[0]))

    if RC:
      self.sig_msg.emit("serialCommunicator : Ouverture comPort {} : RC = {}".format(self.__comPort.portName(), RC))
    else:
      self.sig_msg.emit("serialCommunicator : Erreur à l'ouverture du port série : err# = {0}".format(self.__comPort.error()))


    # Boucle de lecture du port série
    s = ''
    while 1:
      if self.__comPort.waitForReadyRead(20):
        buff = self.__comPort.readAll()
        try:
          s += buff.data().decode()
          # Découpe les données reçues en lignes pour les envoyer une par une
          t = s.splitlines()
        except:
          self.sig_msg.emit("serialCommunicator : Erreur décodage : {}".format(sys.exc_info()[0]))
          s = ''
        if s != '':
          if s[-1] == "\n":
            # La dernière ligne est complette, on envoi tout
            for l in t:
              self.traileLaLigne(l)
            s=''
          else:
            # La dernière ligne est incomplette, on envoi jusqu'à l'avant dernière.
            for l in t[:-1]:
              self.traileLaLigne(l)
            # On laisse la derniere ligne dans le buffer pour qu'elle soit complettée.
            s = t[-1]

      # Process events to receive signals;
      QCoreApplication.processEvents()
      if self.__abort:
        self.sig_msg.emit("serialCommunicator : aborting...")
        break

    # Sortie de la boucle de lecture
    self.sig_msg.emit("serialCommunicator : Fermeture du port série.")
    self.__comPort.close()
    # Emission du signal de fin
    self.sig_done.emit()

  def traileLaLigne(self, l):
    # Envoi de toutes les lignes dans le debug
    self.sig_data_debug.emit(l)
    # Grbl 1.1f ['$' for help] (Init string)
    if l[:5] == "Grbl " and l[-5:] == "help]":
      self.__okToSend = True
      self.__grblStatus = "Idle"
      self.sig_msg.emit("serialCommunicator : Grbl prêt pour recevoir des données")
      self.sig_init.emit(l)
      self.sig_grbl_ok.emit()
    elif l[:1] == "<" and l[-1:] == ">": # Real-time Status Reports
      if self.__grblStatus != l[1:-1].split("|")[0]:
        self.__grblStatus = l[1:-1].split("|")[0]
      self.sig_status.emit(l)
    elif l == "ok": # Reponses "ok"
      if self.__okTrap > 0:
        self.__okTrap -= 1
      else:
        self.sig_ok.emit()
    elif l[:6] == "error:": # "error:X"
      self.sig_response.emit(l)
      self.sig_error.emit()
    elif l[:6] == "ALARM:": # "ALARM:X"
      self.sig_response.emit(l)
      self.sig_alarm.emit()
    else:
      self.sig_data.emit(l)

  @pyqtSlot()
  def isOkToSend(self):
    return self.__okToSend

  @pyqtSlot()
  def grblStatus(self):
    return self.__grblStatus

  @pyqtSlot(str, bool)
  def sendData(self, buff: str, trapOk: bool = False):
    if not self.__okToSend:
      self.sig_msg.emit("serialCommunicator : Erreur : Grbl pas prêt pour recevoir des données")
      return

    if trapOk:
      self.__okTrap = 1 # La prochaine réponse "ok" de Grbl ne sera pas transmise

    ###print("Sending [{}]".format(buff))
    buffWrite = bytes(buff, sys.getdefaultencoding())
    # Temps nécessaire pour la com (millisecondes)
    t_calcul = ceil(1000 * len(buffWrite) * 8 / self.__baudRate) # Arrondi à l'entier supérieur
    timeout = 10 + (2 * t_calcul) # 2 fois le temps nécessaire + 10 millisecondes
    self.__comPort.write(buffWrite)
    if self.__comPort.waitForBytesWritten(timeout):
      self.sig_send_ok.emit()
    else:
      self.sig_msg.emit("serialCommunicator : Erreur envoi des données : timeout")

  @pyqtSlot()
  def abort(self):
    self.sig_msg.emit("serialCommunicator : abort reçu.")
    self.__abort = True
