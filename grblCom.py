# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2021 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file is part of cn5X++                                             '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
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
from cn5X_config import *
from grblComSerial import grblComSerial

GCODE_PARAMETER_OUTPUT_CHANGE_CMD = ["G10", "G28.1", "G30.1", "G38", "G43.1", "G49", "G92"]

class grblCom(QObject):
  '''
  Gestion du thread de communication serie avec Grbl
  '''

  # Reprise des signaux venant du thread de Com a faire suivre
  sig_log        = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string
  sig_connect    = pyqtSignal()         # Emis a la reception de la connexion
  sig_init       = pyqtSignal(str)      # Emis a la reception de la chaine d'initialisation de Grbl, renvoie la chaine complete
  sig_ok         = pyqtSignal()         # Emis a la reception de la chaine "ok"
  sig_error      = pyqtSignal(int)      # Emis a la reception d'une erreur Grbl, renvoie le N° d'erreur
  sig_alarm      = pyqtSignal(int)      # Emis a la reception d'une alarme Grbl, renvoie le N° d'alarme
  sig_status     = pyqtSignal(str)      # Emis a la reception d'un message de status ("<...|.>"), renvoie la ligne complete
  sig_config     = pyqtSignal(str)      # Emis a la reception d'une valeur de config ($XXX)
  sig_data       = pyqtSignal(str)      # Emis a la reception des autres donnees de Grbl, renvoie la ligne complete
  sig_probe      = pyqtSignal(str)      # Emis a la reception d'un résultat de probe
  sig_emit       = pyqtSignal(str)      # Emis a l'envoi des donnees sur le port serie
  sig_recu       = pyqtSignal(str)      # Emis a la reception des donnees sur le port serie
  sig_debug      = pyqtSignal(str)      # Emis a chaque envoi ou reception
  sig_activity   = pyqtSignal(bool)     # Emis a chaque changement de self.__okToSendGCode
  sig_serialLock = pyqtSignal(bool)     # Emis a chaque changement de self.__okToSendGCode

  # Signaux de pilotage a envoyer au thread
  ###sig_abort        = pyqtSignal()
  ###sig_gcodeInsert  = pyqtSignal(str, object)
  ###sig_gcodePush    = pyqtSignal(str, object)
  ###sig_realTimePush = pyqtSignal(str, object)
  ###sig_clearCom     = pyqtSignal()
  ###sig_startPooling = pyqtSignal()
  ###sig_stopPooling  = pyqtSignal()
  ###sig_resetSerial  = pyqtSignal(str)


  def __init__(self):
    super().__init__()
    self.__decode          = None
    self.__threads       = None
    self.__Com           = None
    self.__connectStatus = False
    self.__grblInit      = False
    self.__pooling       = True
    self.__grblVersion   = ""
    self.__grblStatus    = ""
    self.__threads = []
    self.__refreshGcodeParameters = False


  def setDecodeur(self, decodeur):
    self.__decode = decodeur


  def getDecoder(self):
    return self.__decode


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
    newComSerial = grblComSerial(self.__decode, comPort, baudRate, self.__pooling)
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
    newComSerial.sig_probe.connect(self.sig_probe.emit)
    newComSerial.sig_emit.connect(self.sig_emit.emit)
    newComSerial.sig_recu.connect(self.sig_recu.emit)
    newComSerial.sig_debug.connect(self.sig_debug.emit)
    newComSerial.sig_activity.connect(self.sig_activity.emit)
    newComSerial.sig_serialLock.connect(self.sig_serialLock.emit)

    # Signaux de pilotage a envoyer au thread
    ###self.sig_abort.connect(newComSerial.abort)
    ###self.sig_gcodeInsert.connect(newComSerial.gcodeInsert)
    ###self.sig_gcodePush.connect(newComSerial.gcodePush)
    ###self.sig_realTimePush.connect(newComSerial.realTimePush)
    ###self.sig_clearCom.connect(newComSerial.clearCom)
    ###self.sig_startPooling.connect(newComSerial.startPooling)
    ###self.sig_stopPooling.connect(newComSerial.stopPooling)
    ###self.sig_resetSerial.connect(newComSerial.resetSerial)

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
    if self.__refreshGcodeParameters and (self.__grblStatus == GRBL_STATUS_IDLE):
      # Insère la commande Grbl pour relire les paramètres GCode
      ###self.sig_gcodePush.emit(CMD_GRBL_GET_GCODE_PARAMATERS, COM_FLAG_NO_OK | COM_FLAG_NO_ERROR)
      self.__Com.gcodePush(CMD_GRBL_GET_GCODE_PARAMATERS, COM_FLAG_NO_OK | COM_FLAG_NO_ERROR)
      self.__refreshGcodeParameters = False


  def grblStatus(self):
    ''' Renvoi le dernier status Grbl vu '''
    return self.__grblStatus


  def grblInitStatus(self):
    ''' Renvoi le status dinitialisation de Grbl '''
    return self.__grblInit


  def stopCom(self):
    self.sig_debug.emit("grblCom.stopCom(self)")
    ''' Stop le thread des communications serie '''
    self.clearCom() # Vide la file d'attente
    ###self.sig_log.emit(logSeverity.info.value, self.tr("Sending sig_abort signal to serial communications thread..."))
    self.sig_log.emit(logSeverity.info.value, self.tr("Sending abort to serial communications thread..."))
    ###self.sig_abort.emit()
    self.__Com.abort()
    # Attente de la fin du (des) thread(s)
    for thread, worker in self.__threads:
        thread.quit()  # this will quit **as soon as thread event loop unblocks**
        thread.wait()  # <- so you need to wait for it to *actually* quit
    self.sig_log.emit(logSeverity.info.value, self.tr("Child(s) thread(s) terminated."))
    self.__grblInit = False
    self.__threads = []


  def gcodeInsert(self, buff: str, flag=COM_FLAG_NO_FLAG):
    ''' Insertion d'une commande GCode dans la pile en mode LiFo (commandes devant passer devant les autres) '''
    if self.__connectStatus and self.__grblInit:
      ###self.sig_gcodeInsert.emit(buff, flag)
      self.__Com.gcodeInsert(buff, flag)
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl not connected or not initialized, [{}] could not be sent.").format(buff))


  def gcodePush(self, buff: str, flag=COM_FLAG_NO_FLAG):
    ''' Ajout d'une commande GCode dans la pile en mode FiFo (fonctionnement normal de la pile d'un programe GCode) '''
    if self.__connectStatus and self.__grblInit:
      ###self.sig_gcodePush.emit(buff, flag)
      self.__Com.gcodePush(buff, flag)
      QCoreApplication.processEvents()
      # Vérifie si la commande passée modifie les paramètres GCode (resultat de $#)
      for cmd in GCODE_PARAMETER_OUTPUT_CHANGE_CMD:
        if cmd in buff:
          # On relira dès que Grbl sera Idle...
          self.__refreshGcodeParameters = True
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl not connected or not initialized, [{}] could not be sent.").format(buff))


  def realTimePush(self, buff: str, flag=COM_FLAG_NO_FLAG):
    if self.__connectStatus and self.__grblInit:
      ###self.sig_realTimePush.emit(buff, flag)
      self.__Com.realTimePush(buff, flag)
    else:
      self.sig_log.emit(logSeverity.warning.value, self.tr("grblCom: Grbl not connected or not initialized, [{}] could not be sent.").format(buff))


  def clearCom(self):
    ###self.sig_clearCom.emit()
    self.__Com.clearCom()


  @pyqtSlot()
  def startPooling(self):
    self.__pooling = True
    ###self.sig_startPooling.emit()
    self.__Com.startPooling()


  @pyqtSlot()
  def stopPooling(self):
    self.__pooling = False
    ###self.sig_stopPooling.emit()
    self.__Com.stopPooling()

  def isOpen(self):
    return self.__connectStatus


  @pyqtSlot(str)
  def resetSerial(self):
    ###self.sig_resetSerial.emit(buff)
    self.__Com.resetSerial()
