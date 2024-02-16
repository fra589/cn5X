# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_toolChange.py, is part of cn5X++                        '
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

import time, os
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QSettings
from PyQt6.QtWidgets import QDialog, QAbstractButton, QDialogButtonBox, QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, QApplication
from PyQt6.QtGui import QPalette
from cn5X_config import *
#from mainWindow import Ui_mainWindow
from msgbox import *
from grblCom import grblCom
from grblDecode import grblDecode
from grblProbe import *
from cnQPushButton import cnQPushButton


class dlgToolChange(QDialog):
  ''' Classe assurant la gestion de la boite de dialogue changement d'outils '''

  sig_close = pyqtSignal()         # Emis a la fermeture de la boite de dialogue


  def __init__(self, mainWin: QtWidgets.QMainWindow, grbl: grblCom, decoder: grblDecode, axisNumber: int, axisNames: list):
    super().__init__()
    self.di = uic.loadUi(os.path.join(os.path.dirname(__file__), "dlgToolChange.ui"), self)

    self.__mainWin = mainWin
    self.__mainUi  = mainWin.ui

    self.__isVisible = False

    # Paramètres de cn5X++
    self.__settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)

    self.__grblCom   = grbl
    self.__decode    = decoder
    self.__nbAxis    = axisNumber
    self.__axisNames = axisNames
    # Recherche le N° de l'axe Z
    try:
      self.__axisIndexZ = self.__axisNames.index('Z')
    except ValueError:
      self.__axisIndexZ = -1
    self.__probe = grblProbe(self.__grblCom)
    self.__probe.setAxisNames(self.__axisNames)
    self.__probeResult       = None
    self.__initialProbeZ     = False
    self.__initialToolLenght = False

    # Connexion des signaux de l'interface
    self.finished.connect(self.sig_close.emit)
    self.di.btnGo.clicked.connect(self.on_btnGo)
    self.di.btnStop.clicked.connect(self.on_btnStop)
    self.di.btnProbeZ.clicked.connect(self.on_btnProbeZ)
    self.di.btnG49.clicked.connect(self.on_btnG49)
    self.di.btnG43_1.clicked.connect(self.on_btnG43_1)
    self.di.chkInvertProbePin.clicked.connect(self.on_chkInvertProbePin)


  def initialProbeZ(self):
    return self.__initialProbeZ


  def initialToolLenght(self):
    return self.__initialToolLenght


  def setInitialProbeZ(self, val: bool):
    self.__initialProbeZ = val


  def setInitialToolLenght(self, val: bool):
    self.__initialToolLenght = val


  def setAxisNumber(self, axisNumber: int):
    self.__nbAxis    = axisNumber


  def setAxisNames(self, axisNames: list):
    self.__axisNames = axisNames
    self.__probe.setAxisNames(self.__axisNames)


  def isVisible(self):
    return self.__isVisible


  def showDialog(self, toolNum: int = 0):
    ''' Affichage de la boite de dialogue '''
    
    # Message fonction du numéro d'outil à monter
    self.di.lblMessage.setText(self.tr("Insert tool number {}\nand click the 'Go' button\nto continue when ready.".format(toolNum)))

    # Erreur si pas d'axe Z défini
    if self.__axisIndexZ == -1:
      m = msgBox(
                  title  = self.tr("Error !"),
                  text   = self.tr("Z axis is not defined in Grbl!"),
                  icon   = msgIconList.Critical,
                  detail = self.tr("Can't use manual tool change because it's not possible to probe tool length on Z axis.\nAxes definition = [AXS:{}:{}]".format(self.__nbAxis, "".join(self.__axisNames))),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
      return QDialog.Rejected

    # Erreur si Grbl en alarme
    if self.__decode.get_etatMachine() == GRBL_STATUS_ALARM:
      m = msgBox(
                  title  = self.tr("Error !"),
                  text   = self.tr("Grbl is in Alarm mode!"),
                  icon   = msgIconList.Critical,
                  detail = self.tr("Can't tool change because Grbl is in Alarm mode.\nClear Alarm mode before trying to change tool."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
      return QDialog.Rejected

    # Affiche le curseur de souris sablier
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    # Met à jour la case à cocher InvertProbePin
    if self.__decode.getGrblSetting(6) is not None:
      self.di.chkInvertProbePin.setChecked((int(self.__decode.getGrblSetting(6)) == 1))

    # Centrage de la boite de dialogue sur la fenetre principale
    ParentX = self.parent().geometry().x()
    ParentY = self.parent().geometry().y()
    ParentWidth = self.parent().geometry().width()
    ParentHeight = self.parent().geometry().height()
    myWidth = self.geometry().width()
    myHeight = self.geometry().height()
    self.setFixedSize(self.geometry().width(),self.geometry().height())
    self.move(ParentX + int((ParentWidth - myWidth) / 2),ParentY + int((ParentHeight - myHeight) / 2),)
    self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Tool)

    # Attente de la fin du (des) mouvement(s) eventuellement en cours
    tDebut = time.time()
    while (time.time() - tDebut) * 1000 < 2 * GRBL_QUERY_DELAY:
      QCoreApplication.processEvents()
    while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
      QCoreApplication.processEvents()

    # memorise l'état actif de la machine
    self.oldDistanceMode  = self.__decode.getDistanceMode()  # G91/G91
    self.oldEtatSpindle   = self.__decode.get_etatSpindle()  # M5/M3/M4
    self.oldEtatArrosage  = self.__decode.get_etatArrosage() # M9/M7/M8/M78

    # Mémorise la position courante
    self.oldMpos = {}
    for Axis in self.__axisNames:
      self.oldMpos[Axis] = self.__decode.getMpos(Axis)
      # oldMpos de la forme : {'X': 0.0, 'Y': 0.0, 'Z': 0.0, 'A': 0.0, 'B': 0.0}

    # Arrête la broche, l'arrosage et déplace en position de changement d'outils
    self.__decode.set_etatMachine(GRBL_STATUS_RUN)
    self.gotoToolChangePosition()

    # Laisse le temps déplacement vers la position de changement d'outils
    tDebut = time.time()
    while (time.time() - tDebut) * 1000 < 2 * GRBL_QUERY_DELAY:
      QCoreApplication.processEvents()
    while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
      QCoreApplication.processEvents()

    # Restore le curseur de souris
    QApplication.restoreOverrideCursor()

    # Affiche la boite de dialogue
    self.__isVisible = True
    # Using exec() insteed to open() to make the dialog application modal
    RC = self.exec()
    self.__isVisible = False
    return RC


  def on_btnGo(self):
    # restaure l'état de la machine (distance mode, spindle, arrosage)
    if (self.oldDistanceMode != self.__decode.getDistanceMode()):
      self.__grblCom.gcodePush("(Restore distance mode){}".format(self.oldDistanceMode))
    if (self.oldEtatSpindle  != self.__decode.get_etatSpindle()):
      self.__grblCom.gcodePush("(Restore spindle){}".format(self.oldEtatSpindle))
    if self.oldEtatArrosage  != self.__decode.get_etatArrosage():
      if self.oldEtatArrosage == "M78":
        self.__grblCom.gcodePush("(Restore coolant)M7")
        self.__grblCom.gcodePush("(Restore coolant)M8")
      else:
        self.__grblCom.gcodePush("(Restore coolant){}".format(self.oldEtatArrosage))

    # restore la position d'avant le changement d'outils
    # en passant par le Z de dégagement
    posZ = self.__settings.value("Probe/ToolChangePositionZ", DEFAULT_TOOLCHANGE_POSITION_Z, type=float)
    deplacementGCodeZ  = "(Tool change: restoring position)G53G0Z{}".format(posZ)
    self.__grblCom.gcodePush(deplacementGCodeZ)
    axesTraites = ["Z"] # Z traité à part
    gcodeString = "(Tool change: restoring position)G53G0"
    for a in self.__axisNames:
      if a not in axesTraites:
        gcodeString += "{}{}".format(a, self.oldMpos[a])
        axesTraites.append(a)
    self.__grblCom.gcodePush(gcodeString)
    deplacementGCodeZ  = "(Tool change: restoring position)G53G0Z{}".format(self.oldMpos["Z"])
    self.__grblCom.gcodePush(deplacementGCodeZ)

    # ferme la boite de dialogue en envoyant QDialog.Accepted
    self.accept()


  def on_btnStop(self):
    # ANNULATION !
    # ferme la boite de dialogue en envoyant QDialog.Rejected,
    # sans restaurer l'état de la machine ni la position d'outil.
    self.reject()


  def on_chkInvertProbePin(self):
    if self.di.chkInvertProbePin.isChecked():
      self.__grblCom.gcodePush("$6=1")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)
    else:
      self.__grblCom.gcodePush("$6=0")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)


  def on_btnProbeZ(self):
    # Mesure de la longueur d'outil
    
    # retrouve les paramètres de Grbl (vitesses de homing et autres
    # informations de homing qui seront utilisées pour les probes de
    # longueur d'outils)
    homingLocateSpeed = float(self.__decode.getGrblSetting(24)) # Vitesse lente 
    homingSeekSpeed   = float(self.__decode.getGrblSetting(25)) # Vitesse rapide de recherche
    homingPullOff     = float(self.__decode.getGrblSetting(27)) # Distance de retract
    maxTravelZ        = float(self.__decode.getGrblSetting(130 + self.__axisIndexZ))

    # On force le mode relatif
    self.__grblCom.gcodePush("G91")
    
    try:
      # Une première mesure en vitesse rapide de recherche
      self.__probeResult = self.__probe.g38(P=3, F=homingSeekSpeed, Z=-maxTravelZ, g2p=True)
      self.di.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
      self.__mainUi.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
      
      # On dégage de homingPullOff
      self.__grblCom.gcodePush("G0Z{}".format(homingPullOff))
      
      # Deuxieme mesure en vitesse lente
      self.__probeResult = self.__probe.g38(P=3, F=homingLocateSpeed, Z=-1.2*homingPullOff, g2p=True)
      self.di.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
      self.__mainUi.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
      
      # On dégage de homingPullOff
      self.__grblCom.gcodePush("G0Z{}".format(homingPullOff))

    except ValueError as e:
      # Erreur arguments d'appel de self.__probe.g38()
      # L'axe demandé n'est pas dans la liste de self.__axisNames
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnProbeZ(): The requested axis ({}) is not in the axis list of this machine").format(e))
      pass

    except probeError as e:
      # Reception de OK, error ou alarm avant le résultat de probe
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnProbeZ(): {} no response from probe").format(e))
      pass

    except probeFailed as e:
      # Probe action terminée mais sans que la sonde ne touche
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnProbeZ(): {} Probe error").format(e))
      pass

    except speedError as e:
      # Vitesse F non définie, nulle ou négative
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnProbeZ(): F Speed undefined or less or equal to zero").format(e))
      pass

    if (self.__probeResult is not None) and (self.__probeResult.isProbeOK()):
      self.__initialProbeZ = True
      if self.__initialToolLenght:
        self.calculateToolOffset()


  def on_btnG49(self):
    ''' 
    Mémorise le Z du point de contact initial de l'outil pour calculer les outils suivants
    et envoi G49 pour réinitialiser une éventuelle longueur précédente.
    '''
    if not self.__initialProbeZ:
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnG49(): No initial Z probe result, can't get initial tool length probe!"))
      m = msgBox(
                  title  = self.tr("Error !"),
                  text   = self.tr("No initial Z probe result, can't get initial tool length probe!"),
                  info   = self.tr("There was no Z probing previously performed.."),
                  icon   = msgIconList.Critical,
                  detail = self.tr("You must first perform a Z probing of the initial tool to initialize its length."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
      return
    
    # Initialise la longueur d'outil initiale __mainUi
    self.di.lblInitToolLength.setText(self.di.lblLastProbZ.text())
    self.__mainUi.lblInitToolLength.setText(self.di.lblLastProbZ.text())
    # Reset la longueur d'outil Grbl
    self.__grblCom.gcodePush("G49")
    # Réinitialise la différence de longueur d'outil
    toolOffset = self.calculateToolOffset()
    # Flag longueur initiale OK
    self.__initialToolLenght = True


  def on_btnG43_1(self):
    '''
    Calcul de la correction de longueur d'outil par rapport à la valeur initiale mémorisée
    et configure le "Tool Length Offset" dans Grbl à l'aide de G43.1
    '''
    if not self.__initialToolLenght:
      self.__mainWin.log(logSeverity.error.value, self.tr("on_btnG43_1(): No initial tool length, can't calculate length offset!"))
      m = msgBox(
                  title  = self.tr("Error !"),
                  text   = self.tr("No initial tool length, can't calculate length offset!"),
                  info   = self.tr("Initial tool length calculation was not performed.."),
                  icon   = msgIconList.Critical,
                  detail = self.tr("You must first perform a Z probing of the initial tool to initialize its length,\nthen click on the \"Reset/G49\" button,\nthen probing the new tool,\nand finally, click on the \"Send/G43.1\" button."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
      return
    # Calcul et envoi de la correction de longueur d'outil à Grbl
    toolOffset = self.calculateToolOffset()
    toolOffsetGcode = "G43.1Z{}".format(toolOffset)
    self.__grblCom.gcodePush(toolOffsetGcode)


  @pyqtSlot()
  def calculateToolOffset(self):
    # Traitement de la correction de longueur d'outil.
    lastProbe         = float(self.di.lblLastProbZ.text().replace(' ', ''))
    initialToolLength = float(self.di.lblInitToolLength.text().replace(' ', ''))
    toolOffset = lastProbe - initialToolLength
    self.di.lblToolOffset.setText('{:+0.3f}'.format(toolOffset))
    self.__mainUi.lblToolOffset.setText('{:+0.3f}'.format(toolOffset))
    return toolOffset


  def gotoToolChangePosition(self):
    ''' Arrête la broche, l'arrosage et déplace en position de changement d'outils '''
    self.__grblCom.gcodePush("(Tool change)M5")
    self.__grblCom.gcodePush("(Tool change)M9")
    # Recupération des coordonnées Z, X & Y du point
    posZ = self.__settings.value("Probe/ToolChangePositionZ", DEFAULT_TOOLCHANGE_POSITION_Z, type=float)
    posX = self.__settings.value("Probe/ToolChangePositionX", DEFAULT_TOOLCHANGE_POSITION_X, type=float)
    posY = self.__settings.value("Probe/ToolChangePositionY", DEFAULT_TOOLCHANGE_POSITION_Y, type=float)
    # Effectue les déplacements
    deplacementGCodeZ  = "(Goto tool change Z)G53G0Z{}".format(posZ)
    deplacementGCodeXY = "(Goto tool change XY)G53G0X{}Y{}".format(posX, posY)
    self.__grblCom.gcodePush(deplacementGCodeZ)
    self.__grblCom.gcodePush(deplacementGCodeXY)

