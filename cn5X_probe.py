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

from PyQt5 import QtCore
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal, pyqtSlot
from cn5X_config import *
from grblCom import grblCom


class grblProbe(QObject):
  ''' Classe de gestion du palpage (probe) '''

  # Communication inter objets :
  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant grblComSerial, renvoie : logSeverity, message string

  def __init__(self, grbl: grblCom):
    super().__init__()
    self.__grblCom   = grbl
    self.__axisNames = []
    self.__lastProbe = probeResult()

    self.__ok_recu       = False
    self.__error_recu    = False
    self.__alarm_recu    = False
    self.__probe_recu    = False
    self.__probe_attendu = False

    self.__grblCom.sig_ok.connect(self.on_sig_ok)
    self.__grblCom.sig_error.connect(self.on_sig_error)
    self.__grblCom.sig_alarm.connect(self.on_sig_alarm)
    self.__grblCom.sig_probe.connect(self.on_sig_probe)


  @pyqtSlot()
  def on_sig_ok(self):
    self.__ok_recu    = True


  @pyqtSlot(int)
  def on_sig_error(self, errNum: int):
    self.__error_recu = True


  @pyqtSlot(int)
  def on_sig_alarm(self, alarmNum: int):
    self.__alarm_recu = True


  @pyqtSlot(str)
  def on_sig_probe(self, data: str):
    if self.__probe_attendu:
      tblData   = data.split(":")
      tblValues = tblData[1].split(",")
      if tblData[2] == "1]":
        self.__lastProbe.setProbeOK(True)
      else:
        self.__lastProbe.setProbeOK(False)
      num = 0
      for v in tblValues:
        if num > 5:
          self.sig_log.emit(logSeverity.warning.value, self.tr("grblProbe.on_sig_probe(): Warning: Grbl probe response have more than 6 axis. Values of axis number > 6 are ommited!"))
          break
        self.__lastProbe.setAxis(num, v)
        num += 1
      self.__probe_attendu = False
      self.__probe_recu = True


  def setAxisNames(self, axisNames:list):
    self.__axisNames = axisNames
    self.__lastProbe.setAxisNames(axisNames)


  def g38(self, P:int=0, 
                X:float=None, Y:float=None, Z:float=None, 
                A:float=None, B:float=None, C:float=None, 
                U:float=None, V:float=None, W:float=None, 
                F=0, 
                g2p:bool=False
         ):
    '''
    Probe routine, P = mantisse du G38 => 2, 3, 4 ou 5 :
    - 2 => G38.2 = palpe vers la pièce, stoppe au toucher, signale une erreur en cas de défaut. 
    - 3 => G38.3 = palpe vers la pièce, stoppe au toucher.
    - 4 => G38.4 = palpe en quittant la pièce, stoppe en perdant le contact, signal une erreur en cas de défaut.
    - 5 => G38.5 = palpe en quittant la pièce, stoppe en perdant le contact.
    - X, Y, Z, A, B, C, U, V & W : Destination vers laquelle on palpe à partir du point courant,
    - g2p = True => effectue un déplacement aux coordonnées palpées (le probe s'arrête légèrement après le 
      contact en fonction de la décélération, donc, on retourne au point palpé).
      si g2p = False (par défaut), pas de déplacement après palpage.
    '''
    
    # On lance un nouveau Probe on ne sait pas s'il sera OK...
    self.__lastProbe.setProbeOK(False)
    
    # Vérification des arguments, les nom d'axes demandés dans les mouvements doivent exister dans Grbl
    if P<2 or P>5:
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'P' must be 2, 3, 4 or 5 for respectively G38.2, G38.3, G38.4 or G38.5."))
      return
    if (X is not None) and ('X' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'X' is not in the axisNames list."))
      return
    if (Y is not None) and ('Y' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'Y' is not in the axisNames list."))
      return
    if (Z is not None) and ('Z' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'Z' is not in the axisNames list."))
      return
    if (A is not None) and ('A' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'A' is not in the axisNames list."))
      return
    if (B is not None) and ('B' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'B' is not in the axisNames list."))
      return
    if (C is not None) and ('C' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'C' is not in the axisNames list."))
      return
    if (U is not None) and ('U' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'U' is not in the axisNames list."))
      return
    if (V is not None) and ('V' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'V' is not in the axisNames list."))
      return
    if (W is not None) and ('W' not in self.__axisNames):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: 'W' is not in the axisNames list."))
      return
    if F <= 0:
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): ArgumentError: Probe speed: F undefinied or null."))
      return
    # Vérification que Grl est bien connecté et initialisé 
    if (not self.__grblCom.isOpen) or (not self.__grblCom.grblInitStatus):
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): Error: Grbl is not connected or not initialized."))
      return
    # Récupération et vérification du décodeur
    self.__decode = self.__grblCom.getDecoder()
    if self.__decode is None:
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): cn5X++ error: no active Grbl decoder, this should never happen!?!?"))
      return

    # Construction de l'ordre probe
    probeGCode = "G38.{}F{}".format(P, F)
    if X is not None:
      probeGCode += "X{}".format(X)
    if Y is not None:
      probeGCode += "Y{}".format(Y)
    if Z is not None:
      probeGCode += "Z{}".format(Z)
    if A is not None:
      probeGCode += "A{}".format(A)
    if B is not None:
      probeGCode += "B{}".format(B)
    if C is not None:
      probeGCode += "C{}".format(C)
    if U is not None:
      probeGCode += "U{}".format(U)
    if V is not None:
      probeGCode += "V{}".format(V)
    if W is not None:
      probeGCode += "W{}".format(W)

    # On se prépare à attendre la réponse...
    self.__probe_attendu = True
    self.__ok_recu       = False
    self.__error_recu    = False
    self.__alarm_recu    = False
    self.__probe_recu    = False
    self.__lastProbe.setProbeOK(False)
    
    # On prévient le communicator qu'on attend le résultat
    self.__grblCom.getDecoder().getNextProbe()
    
    # Envoi du GCode à Grbl
    self.__grblCom.gcodePush(probeGCode)
    
    # Attente du résultat
    while not self.__probe_recu:
      # Process events to receive signals;
      QCoreApplication.processEvents()
      if (self.__ok_recu or self.__error_recu or self.__alarm_recu) and (not self.__probe_recu):
        self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): Probe error: No probe response before OK, error or Alarm!"))
        return

    self.sig_log.emit(logSeverity.info.value, self.tr("grblProbe.g38(): Response probe received."))

    if not self.__lastProbe.isProbeOK():
      self.sig_log.emit(logSeverity.error.value, self.tr("grblProbe.g38(): Error: Last probe failure"))

    else: # Probe OK.
      # Déplacement éventuel après probe OK pour revenir au point exact.
      # Le probe renvoie les coordonnées machine du point, d'ou l'utilisation de G53
      if g2p:
        retractGCode = "G53G1F{}".format(F)
        if X is not None: # On ne se déplace que sur les axes utilisés par le palpage
          retractGCode += "X{}".format(self.__lastProbe.getAxisByName("X"))
        if Y is not None:
          retractGCode += "Y{}".format(self.__lastProbe.getAxisByName("Y"))
        if Z is not None:
          retractGCode += "Z{}".format(self.__lastProbe.getAxisByName("Z"))
        if A is not None:
          retractGCode += "A{}".format(self.__lastProbe.getAxisByName("A"))
        if B is not None:
          retractGCode += "B{}".format(self.__lastProbe.getAxisByName("B"))
        if C is not None:
          retractGCode += "C{}".format(self.__lastProbe.getAxisByName("C"))
        if U is not None:
          retractGCode += "U{}".format(self.__lastProbe.getAxisByName("U"))
        if V is not None:
          retractGCode += "V{}".format(self.__lastProbe.getAxisByName("V"))
        if W is not None:
          retractGCode += "W{}".format(self.__lastProbe.getAxisByName("W"))

        # Envoi du GCode à Grbl
        self.__grblCom.gcodePush(retractGCode)

    return self.__lastProbe


class probeResult(QObject):
  ''' Objet de stockage d'un résultat de probe. Stocke les 6 valeurs d'axes ainsi que le statut du probe '''
  
  def __init__(self):
    super().__init__()
    self.__axis = [None,None,None,None,None,None]
    '''self.__axis[0] = None
    self.__axis[1] = None
    self.__axis[2] = None
    self.__axis[3] = None
    self.__axis[4] = None
    self.__axis[5] = None'''
    self.__probeOK = False
    self.__axisNames = ""


  def setAxisNames(self, names: list):
    self.__axisNames = names


  def setAxis(self, num: int, value: float):
    '''Stocke une valeur d'axe'''
    if num < 0 or num > 5:
      raise ValueError("steAxisValue(): axisNum must be between 0 and 5")
    self.__axis[num] = value


  def getAxis(self, num: int):
    '''Stocke une valeur d'axe'''
    if num < 0 or num > 5:
      raise ValueError("steAxisValue(): axisNum must be between 0 and 5")
    return self.__axis[num]


  def getAxisByName(self, name: str):
    if name in self.__axisNames:
      return self.__axis[self.__axisNames.index(name)]


  def setProbeOK(self, value: bool):
    self.__probeOK = value


  def isProbeOK(self):
    return self.__probeOK


#

