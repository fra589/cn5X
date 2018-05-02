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
from enum import Enum
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from cn5X_config import *
from grblComStack import grblStack


class grblComSerial(QObject):
  '''
  QObject worker assurant la gestion de la communication série bidirectionnelle entre cn5X++ et grbl.
  Doit être executé dans son propre thread pour ne pas bloquer l'interface graphique.
  '''

  sig_connect = pyqtSignal(bool)     # Message emis à la connexion (valeur = True) et à la déconnexion ou en cas d'erreur de connexion (valeur = False)
  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string
  sig_init    = pyqtSignal(str)      # Emis à la réception de la chaine d'initialisation de Grbl, renvoie la chaine complète
  sig_ok      = pyqtSignal()         # Emis à la réception de la chaine "ok"
  sig_error   = pyqtSignal(int)      # Emis à la réception d'une erreur Grbl, renvoie le N° d'erreur
  sig_alarm   = pyqtSignal(int)      # Emis à la réception d'une alarme Grbl, renvoie le N° d'alarme
  sig_status  = pyqtSignal(str)      # Emis à la réception d'un message de status ("<...|.>"), renvoie la ligne complète
  sig_config  = pyqtSignal(str)      # Emis à la réception d'une valeur de config ($XXX)
  sig_data    = pyqtSignal(str)      # Emis à la réception des autres données de Grbl, renvoie la ligne complète
  sig_emit    = pyqtSignal(str)      # Emis à l'envoi des données sur le port série
  sig_recu    = pyqtSignal(str)      # Emis à la réception des données sur le port série
  sig_debug   = pyqtSignal(str)      # Emis à chaque envoi ou réception


  def __init__(self, comPort: str, baudRate: int):
    super().__init__()

    self.__abort            = False
    self.__portName         = comPort
    self.__baudRate         = baudRate

    self.__realTimeStack    = grblStack()
    self.__mainStack        = grblStack()

    self.__initOK           = False
    self.__grblStatus       = ""

    self.__queryCounter     = 0
    self.__querySequence    = [
      REAL_TIME_REPORT_QUERY,
      REAL_TIME_REPORT_QUERY,
      CMD_GRBL_GET_GCODE_PARAMATERS + '\n',
      REAL_TIME_REPORT_QUERY,
      REAL_TIME_REPORT_QUERY,
      CMD_GRBL_GET_GCODE_STATE + '\n'
    ]
    self.__lastQueryTime    = time.time()


  @pyqtSlot()
  def abort(self):
    ''' Traitement du signal demandant l'arrêt de la communication '''
    self.sig_log.emit(logSeverity.info.value, "serialCommunicator : abort reçu.")
    self.__abort = True


  @pyqtSlot()
  def clearCom(self):
    ''' Vide les files d'attente '''
    self.__realTimeStack.clear()
    self.__mainStack.clear()


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def realTimePush(self, buff: str, flag = COM_FLAG_NO_FLAG):
    ''' Ajout d'une commande GCode dans la pile en mode FiFo '''
    self.__realTimeStack.addFiFo(buff, flag)


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def gcodePush(self, buff: str, flag = COM_FLAG_NO_FLAG):
    ''' Ajout d'une commande GCode dans la pile en mode FiFo (fonctionnement normal de la pile d'un programe GCode) '''
    self.__mainStack.addFiFo(buff, flag)


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def gcodeInsert(self, buff: str, flag = COM_FLAG_NO_FLAG):
    ''' Insertion d'une commande GCode dans la pile en mode LiFo (commandes devant passer devant les autres) '''
    self.__mainStack.addLiFo(buff, flag)


  def __sendData(self, buff: str):
    ''' Envoie des données sur le port série '''
    # Signal debug pour toutes les données envoyées
    if buff[-1:] == "\n":
      self.sig_debug.emit(">>> " + buff[:-1] + "\\n")
    elif buff[-2:] == "\r\n":
      self.sig_debug.emit(">>> " + buff[:-2] + "\\r\\n")
    else:
      self.sig_debug.emit(">>> " + buff)
    # Formatage du buffer à envoyer
    buffWrite = bytes(buff, sys.getdefaultencoding())
    # Temps nécessaire pour la com (millisecondes), arrondi à l'entier supérieur
    tempNecessaire = ceil(1000 * len(buffWrite) * 8 / self.__baudRate)
    timeout = 10 + (2 * tempNecessaire) # 2 fois le temps nécessaire + 10 millisecondes
    # Ecriture sur le port série
    self.__comPort.write(buffWrite)
    if self.__comPort.waitForBytesWritten(timeout):
      ### remonté en amon dans la boucle principale self.sig_emit.emit(buff)
      pass
    else:
      self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur envoi des données : timeout, err# = {0}".format(self.__comPort.error()))


  def __traileLaLigne(self, l, flag = COM_FLAG_NO_FLAG):
    ''' Emmet les signaux ad-hoc pour toutes les lignes reçues  '''
    # Envoi de toutes les lignes dans le debug
    if l[-1:] == "\n":
      self.sig_debug.emit("<<< " + l[:-1] + "\\n")
    elif l[-2:] == "\r\n":
      self.sig_debug.emit("<<< " + l[:-2] + "\\r\\n")
    else:
      self.sig_debug.emit("<<< " + l)
    # Premier décodage pour envoyer le signal ah-hoc
    if l[:5] == "Grbl " and l[-5:] == "help]": # Init string : Grbl 1.1f ['$' for help]
      self.sig_init.emit(l)
    elif l == "ok":                            # Reponses "ok"
      if not flag & COM_FLAG_NO_OK:
        self.sig_ok.emit()
    elif l[:6] == "error:":                    # "error:X" => Renvoie X
      if not flag & COM_FLAG_NO_ERROR:
        errNum = int(l.split(':')[1])
        self.sig_error.emit(errNum)
    elif l[:6] == "ALARM:":                    # "ALARM:X" => Renvoie X
      alarmNum = int(l.split(':')[1])
      self.sig_alarm.emit(alarmNum)
    elif l[:1] == "<" and l[-1:] == ">":       # Real-time Status Reports
      self.__grblStatus = l[1:].split('|')[0]
      self.sig_status.emit(l)
    elif l[:1] == "$" or l[:5] == "[VER:" or l[:5] == "[AXS:" or l[:5] == "[OPT:": # Setting output
      self.sig_config.emit(l)
    else:
      self.sig_data.emit(l)


  def __openComPort(self):
    ''' Ouverture du port série et attente de la chaine d'initialisation en provenence de Grbl '''

    openMaxTime = 5000 # (ms) Timeout pour recevoir la réponse de Grbl après ouverture du port = 5 secondes

    # Configuration du port
    self.__comPort  = QSerialPort()
    self.__comPort.setPortName(self.__portName)
    self.__comPort.setBaudRate(self.__baudRate)
    self.__comPort.setDataBits(QSerialPort.Data8)
    self.__comPort.setStopBits(QSerialPort.OneStop)
    self.__comPort.setParity(QSerialPort.NoParity)

    # Ouverture du port
    RC = False
    try:
      RC = self.__comPort.open(QIODevice.ReadWrite)
    except OSError as err:
      self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur ouverture du port : {0}".format(err))
      self.sig_connect.emit(False)
      return False
    except:
      self.sig_log.emit(logSeverity.error.value, "grblComSerial : Unexpected error : {}".format(sys.exc_info()[0]))
      self.sig_connect.emit(False)
      return False
    if not RC:
      self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur à l'ouverture du port série : err# = {0}".format(self.__comPort.error()))
      self.sig_connect.emit(False)
      return False

    # Ouverture du port OK
    self.sig_connect.emit(True)
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : comPort {} ouvert, RC = {}".format(self.__comPort.portName(), RC))

    # Attente initialisatoin Grbl
    tDebut = time.time() * 1000
    while True:
      serialData = ""
      while serialData == "" or serialData[-1] != '\n':
        if self.__comPort.waitForReadyRead(25):
          buff = self.__comPort.readAll()
          self.sig_debug.emit("Buffer recu : " + str(buff))
          try:
            newData = buff.data().decode()
            serialData += newData
          except:
            self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur décodage : {}".format(sys.exc_info()[0]))
        now = time.time() * 1000
        if now > tDebut + openMaxTime:
          self.sig_log.emit(logSeverity.error.value, "grblComSerial : Initialisation de Grbl : Timeout !")
          self.__comPort.close()
          return False
      # On cherche la chaine d'initialisation dans les lignes du buffer
      for l in serialData.splitlines():
        if l[:5] == "Grbl " and l[-5:] == "help]": # Init string : Grbl 1.1f ['$' for help]
          self.sig_init.emit(l)
          self.__initOK = True
        elif self.__initOK:
          self.sig_data.emit(l)
      if self.__initOK:
        return True # On a bien reçu la chaine d'initialisation de Grbl

  def __mainLoop(self):
    ''' Boucle principale du composant : lectures / écritures sur le port série '''
    okToSendGCode = True
    while True:
      # On commence par vider la file d'attente des commandes temps réel
      while not self.__realTimeStack.isEmpty():
        toSend, flag = self.__realTimeStack.pop()
        self.__sendData(toSend)
      if okToSendGCode:
        # Envoi d'une ligne gcode si en attente
        if not self.__mainStack.isEmpty():
          # La pile n'est pas vide, on envoi la prochaine commande récupérée dans la pile GCode
          toSend, flag = self.__mainStack.pop()
          if toSend[-1:] != '\n':
            toSend += '\n'
          if not flag & COM_FLAG_NO_OK:
            if toSend[-2:] == '\r\n':
              self.sig_emit.emit(toSend[:-2])
            else:
              self.sig_emit.emit(toSend[:-1])
          self.__sendData(toSend)
          okToSendGCode = False # On enverra plus de commande tant que l'on aura pas reçu l'accusé de réception.
      # Lecture du port série
      serialData = ""
      while True:
        if self.__comPort.waitForReadyRead(25):
          buff = self.__comPort.readAll()
          try:
            newData = buff.data().decode()
            serialData += newData
          except:
            self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur décodage : {}".format(sys.exc_info()[0]))
          if serialData != "" and serialData[-1] == '\n':
            dataAvailable = True
            break # La dernière ligne reçue est complette
        else:
          dataAvailable = False
          # Process events to receive signals;
          QCoreApplication.processEvents()
          break
      if dataAvailable:
        # Découpe les données reçues en lignes pour les envoyer une par une
        tblLines = serialData.splitlines()
        for l in tblLines:
          if l.find('ok') >= 0 or l.find('error') >= 0:
            okToSendGCode = True # Accusé de réception ou erreur de la dernière commande GCode envoyée
          if l !='':
            self.__traileLaLigne(l, flag)
      if self.__abort:
        self.sig_log.emit(logSeverity.info.value, "grblComSerial : quitting...")
        break # Sortie de la boucle principale

      # Intérrogations de Grbl à interval régulier selon la séquence définie par self.__querySequence
      if (time.time() - self.__lastQueryTime) * 1000 > GRBL_QUERY_DELAY and self.__initOK:
        if len(self.__querySequence[self.__queryCounter]) == 1:
          self.realTimePush(self.__querySequence[self.__queryCounter])
        else:
          if self.__grblStatus == "Idle":
            self.gcodeInsert(self.__querySequence[self.__queryCounter], COM_FLAG_NO_OK | COM_FLAG_NO_ERROR)
        self.__lastQueryTime    = time.time()
        self.__queryCounter += 1
        if self.__queryCounter >= len(self.__querySequence):
          self.__queryCounter = 0

    # On est sorti de la boucle principale : fermeture du port.
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : Fermeture du port série.")
    self.sig_connect.emit(False)
    self.__comPort.close()
    self.__initOK = False
    # Emission du signal de fin
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : End.")


  def run(self):
    ''' Démarre la communication avec le port série dans un thread séparé '''

    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_log.emit(logSeverity.info.value, 'grblComSerial running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    if self.__openComPort():
      self.__mainLoop()
    else:
      self.sig_log.emit(logSeverity.error.value, "grblComSerial : impossible d'ouvrir le port série !")
      # Emission du signal de fin
      self.sig_log.emit(logSeverity.info.value, "grblComSerial : End.")





