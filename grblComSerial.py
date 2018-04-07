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
from enum import Enum
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from cn5X_config import *
from grblComStack import grblStack


class grblComSerial(QObject):
  '''
  QObject worker assurant la gestion de la communication série bidirectionnelle entre cn5X et grbl.
  Doit être executé dans son propre thread pour ne pas bloquer l'interface graphique.
  '''

  sig_connect = pyqtSignal(bool)     # Message emis à la connexion (valeur = True) et à la déconnexion ou en cas d'erreur de connexion (valeur = False)
  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string
  sig_init    = pyqtSignal(str)      # Emis à la réception de la chaine d'initialisation de Grbl, renvoie la chaine complète
  sig_ok      = pyqtSignal()         # Emis à la réception de la chaine "ok"
  sig_error   = pyqtSignal(int)      # Emis à la réception d'une erreur Grbl, renvoie le N° d'erreur
  sig_alarm   = pyqtSignal(int)      # Emis à la réception d'une alarme Grbl, renvoie le N° d'alarme
  sig_status  = pyqtSignal(str)      # Emis à la réception d'un message de status ("<...|.>"), renvoie la ligne complète
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

  def run(self):

    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_log.emit(logSeverity.info.value, 'grblComSerial running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    # Configuration du port série
    self.__comPort  = QSerialPort()
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

    self.sig_connect.emit(True)
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : comPort {} ouvert, RC = {}".format(self.__comPort.portName(), RC))

    # Boucle principale du composant
    flag = None
    while 1:
      # On commence par vider la file d'attente et envoyer les commandes temps réel
      while not self.__realTimeStack.isEmpty():
        toSend, flag = self.__realTimeStack.pop()
        self.__sendData(toSend)
      # Ensuite, on envoie une ligne gcode en attente
      if not self.__mainStack.isEmpty():
        # Si la pile n'est pas vide, on envoi la prochaine commande et on attend la réponse
        toSend, flag = self.__mainStack.pop()
        if toSend[-1:] != '\n':
          toSend += '\n'
        if flag != "NO_OK":
          if toSend[-2:] == '\c\n':
            self.sig_emit.emit(toSend[:-2])
          else:
            self.sig_emit.emit(toSend[:-1])
        self.__sendData(toSend)
        # Boucle 1 de lecture du port série
        serialData = ''
        newData    = ''
        foundErrorOk = False
        while 1:
          if self.__comPort.waitForReadyRead(25):
            buff = self.__comPort.readAll()
            try:
              newData = buff.data().decode()
            except:
              self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur décodage : {}".format(sys.exc_info()[0]))
            serialData = serialData + newData

            if serialData != '':
              self.sig_recu.emit(serialData)
              # Découpe les données reçues en lignes pour les envoyer une par une
              tblLines = serialData.splitlines()
              if serialData[-1] != "\n":
                # La dernière ligne est incomplette, on envoi jusqu'à l'avant dernière.
                for l in tblLines[:-1]:
                  if l.find('ok') >= 0 or l.find('error') >= 0: foundErrorOk = True
                  if l !='':
                    if l[0] != '<' and l[-1] == ">": self.sig_log.emit(logSeverity.error.value, "Erreur de découpage en position 1 ({})".format(l))
                  self.__traileLaLigne(l, flag)
                # On laisse la derniere ligne dans le buffer pour qu'elle soit complettée.
                serialData = tblLines[-1]
              else:
                # La dernière ligne est complette, on envoi tout
                for l in tblLines:
                  if l.find('ok') >= 0 or l.find('error') >= 0: foundErrorOk = True
                  if l !='':
                    if l[0] != '<' and l[-1] == ">": self.sig_log.emit(logSeverity.error.value, "Erreur de découpage en position 2 ({})".format(l))
                  self.__traileLaLigne(l, flag)
                serialData=''
                if foundErrorOk:
                  # On à eu la réponse de Grbl, on peux passer au prochain envoi.
                  break
          # Process events to receive signals;
          QCoreApplication.processEvents()
          if self.__abort:
            self.sig_log.emit(logSeverity.warning.value, "grblComSerial : aborting while waiting for Grbl response...")
            break # Sortie de la boucle de lecture

          # On a pas fini d'attendre la réponse de Grbl, on traite le temps réel s'il y en a en attente
          while not self.__realTimeStack.isEmpty():
            toSend, flag = self.__realTimeStack.pop()
            self.__sendData(toSend)

          # Intérrogations de Grbl à interval régulier selon la séquence définie par self.__querySequence
          if (time.time() - self.__lastQueryTime) * 1000 > GRBL_QUERY_DELAY and self.__initOK:
            if len(self.__querySequence[self.__queryCounter]) == 1:
              self.realTimePush(self.__querySequence[self.__queryCounter])
            else:
              if self.__grblStatus == "Idle":
                self.gcodeInsert(self.__querySequence[self.__queryCounter], "NO_OK")
            self.__lastQueryTime    = time.time()
            self.__queryCounter += 1
            if self.__queryCounter >= len(self.__querySequence):
              self.__queryCounter = 0

      else:
        # La file d'attente est vide, on regarde quand même si Grbl nous envoie des infos
        # Boucle 2 de lecture du port série
        serialData = ''
        newData    = ''
        while 1:
          if self.__comPort.waitForReadyRead(25):
            buff = self.__comPort.readAll()
            try:
              newData = buff.data().decode()
            except:
              self.sig_log.emit(logSeverity.error.value, "grblComSerial : Erreur décodage : {}".format(sys.exc_info()[0]))
            serialData = serialData + newData

            if serialData != '':
              self.sig_recu.emit(serialData)
              # Découpe les données reçues en lignes pour les envoyer une par une
              tblLines = serialData.splitlines()
              if serialData[-1] != "\n":
                # La dernière ligne est incomplette, on envoi jusqu'à l'avant dernière.
                for l in tblLines[:-1]:
                  if l !='':
                    if l[0] != '<' and l[-1] == ">": self.sig_log.emit(logSeverity.error.value, "Erreur de découpage en position 3 ({})".format(l))
                  self.__traileLaLigne(l, flag)
                # On laisse la derniere ligne dans le buffer pour qu'elle soit complettée.
                serialData = tblLines[-1]
                ###print("Données restantes ***{}***".format(serialData))
              else:
                # La dernière ligne est complette, on envoi tout
                for l in tblLines:
                  if l !='':
                     if l[0] != '<' and l[-1] == ">":
                       self.sig_log.emit(logSeverity.error.value, "Erreur de découpage en position 4 ({})".format(l))
                  self.__traileLaLigne(l, flag)
                serialData=''
                # On à eu une ou plusieurs lignes complettes de Grbl, on peux passer au prochain envoi.
                break
          # Process events to receive signals;
          QCoreApplication.processEvents()
          if self.__abort:
            self.sig_log.emit(logSeverity.warning.value, "grblComSerial : aborting while waiting for Grbl response...")
            break # Sortie de la boucle de lecture

          # Intérrogations de Grbl à interval régulier selon la séquence définie par self.__querySequence
          if (time.time() - self.__lastQueryTime) * 1000 > GRBL_QUERY_DELAY and self.__initOK:
            if len(self.__querySequence[self.__queryCounter]) == 1:
              self.realTimePush(self.__querySequence[self.__queryCounter])
            else:
              if self.__grblStatus == "Idle":
                self.gcodeInsert(self.__querySequence[self.__queryCounter], "NO_OK")
            self.__lastQueryTime    = time.time()
            self.__queryCounter += 1
            if self.__queryCounter >= len(self.__querySequence):
              self.__queryCounter = 0

          # Si une des 2 file d'attente n'est pas vide, on repart dans la boucle 1
          if (not self.__mainStack.isEmpty() or not self.__realTimeStack.isEmpty()) and serialData == '':
            break

      if self.__abort:
        self.sig_log.emit(logSeverity.info.value, "grblComSerial : quitting...")
        break # Sortie de la boucle principale

    # Sortie de la boucle principale
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : Fermeture du port série.")
    self.sig_connect.emit(False)
    self.__comPort.close()
    self.__initOK = False
    # Emission du signal de fin
    self.sig_log.emit(logSeverity.info.value, "grblComSerial : End.")


  def __sendData(self, buff: str):
    ''' Envoie des données sur le port série '''

    # Envoi de toutes les lignes dans le debug
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


  def __traileLaLigne(self, l, flag = None):
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
      self.__initOK = True
    elif l == "ok":                            # Reponses "ok"
      if flag != "NO_OK":
        self.sig_ok.emit()
    elif l[:6] == "error:":                    # "error:X" => Renvoie X
      errNum = int(l.split(':')[1])
      self.sig_error.emit(errNum)
    elif l[:6] == "ALARM:":                    # "ALARM:X" => Renvoie X
      alarmNum = int(l.split(':')[1])
      self.sig_alarm.emit(alarmNum)
    elif l[:1] == "<" and l[-1:] == ">":       # Real-time Status Reports
      self.__grblStatus = l[1:].split('|')[0]
      self.sig_status.emit(l)
    else:
      self.sig_data.emit(l)


  @pyqtSlot()
  def abort(self):
    self.sig_log.emit(logSeverity.info.value, "serialCommunicator : abort reçu.")
    self.__abort = True


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def gcodePush(self, buff: str, flag = None):
    ''' Ajout d'une commande GCode dans la pile en mode FiFo (fonctionnement normal de la pile d'un programe GCode) '''
    self.__mainStack.addFiFo(buff, flag)


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def gcodeInsert(self, buff: str, flag = None):
    ''' Insertion d'une commande GCode dans la pile en mode LiFo (commandes devant passer devant les autres) '''
    self.__mainStack.addLiFo(buff, flag)


  @pyqtSlot(str)
  @pyqtSlot(str, object)
  def realTimePush(self, buff: str, flag = None):
    ''' Ajout d'une commande GCode dans la pile en mode FiFo '''
    self.__realTimeStack.addFiFo(buff, flag)


  @pyqtSlot()
  def clearCom(self):
    ''' Vide les files d'attente '''
    self.__realTimeStack.clear()
    self.__mainStack.clear()








