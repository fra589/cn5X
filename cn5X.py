# !/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
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
import sys, os, time #, datetime
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, QThread, pyqtSignal, pyqtSlot, QModelIndex,  QItemSelectionModel
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDialog, QAbstractItemView
from PyQt5.QtSerialPort import QSerialPortInfo
from cn5X_config import *
from msgbox import *
from speedOverrides import *
from grblCom import grblCom
from grblDecode import grblDecode
from gcodeQLineEdit import gcodeQLineEdit
from cnQPushButton import cnQPushButton
from grblJog import grblJog
from cn5X_gcodeFile import gcodeFile
from grblConfig import grblConfig
import mainWindow

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="sélection du port série")
    parser.add_argument("-c", "--connect", action="store_true", help="Connecte le port série")
    parser.add_argument("-u", "--noUrgentStop", action="store_true", help="Désactive l'arrêt d'urgence")
    parser.add_argument("-f", "--file", help="Charge le fichier GCode")
    self.__args = parser.parse_args()

    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)
    self.logGrbl  = self.ui.txtGrblOutput    # Tous les messages de Grbl seront redirigés dans le widget txtGrblOutput
    self.logCn5X  = self.ui.txtConsoleOutput # Tous les messages applicatif seront redirigés dans le widget txtConsoleOutput
    self.logDebug = self.ui.txtDebugOutput   # Message debug de Grbl

    self.logGrbl.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes
    self.logCn5X.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes
    self.logDebug.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes
    self.ui.grpConsole.setCurrentIndex(2) # Active l'index de la log cn5X++

    self.__gcodeFile = gcodeFile(self.ui.gcodeTable)
    self.__gcodeFile.sig_log.connect(self.on_sig_log)

    self.timerDblClic = QtCore.QTimer()

    self.__grblCom = grblCom()
    self.__grblCom.sig_log.connect(self.on_sig_log)
    self.__grblCom.sig_connect.connect(self.on_sig_connect)
    self.__grblCom.sig_init.connect(self.on_sig_init)
    self.__grblCom.sig_ok.connect(self.on_sig_ok)
    self.__grblCom.sig_error.connect(self.on_sig_error)
    self.__grblCom.sig_alarm.connect(self.on_sig_alarm)
    self.__grblCom.sig_status.connect(self.on_sig_status)
    self.__grblCom.sig_config.connect(self.on_sig_config)
    self.__grblCom.sig_data.connect(self.on_sig_data)
    self.__grblCom.sig_emit.connect(self.on_sig_emit)
    self.__grblCom.sig_recu.connect(self.on_sig_recu)
    self.__grblCom.sig_debug.connect(self.on_sig_debug)

    self.decode = grblDecode(self.ui, self.log, self.__grblCom)

    self.__jog = grblJog(self.__grblCom)

    self.__connectionStatus = False
    self.__arretUrgence     = True
    self.__cycleRun         = False
    self.__cyclePause       = False
    self.__grblConfigLoaded = False
    self.__nbAxis           = 0
    self.__axisNames        = []

    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(pathname)

    """---------- Préparation de l'interface ----------"""
    QtGui.QFontDatabase.addApplicationFont(":/cn5X/fonts/LEDCalculator.ttf")  # Police type "LED"
    self.ui.btnConnect.setText("Connecter")                                   # Label du bouton connect
    self.populatePortList()                                                   # On rempli la liste des ports série

    app.setStyleSheet("QToolTip { background-color: rgb(248, 255, 192); color: rgb(0, 0, 63); }")

    curIndex = -1                                                             # On rempli la liste des vitesses
    for v in QSerialPortInfo.standardBaudRates():
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == COM_DEFAULT_BAUD_RATE:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenêtre (status bar)
    self.__statusText = ""
    self.ui.statusBar.showMessage(self.__statusText)

    # Positionne l'état d'activation des contrôles
    self.setEnableDisableGroupes()

    """---------- Connections des évennements de l'interface graphique ----------"""
    self.ui.btnUrgence.pressed.connect(self.on_arretUrgence)             # Evenements du bouton d'arrêt d'urgence
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed) # un clic sur un élément de la liste appellera la méthode 'on_cmbPort_changed'

    self.ui.mnuBar.hovered.connect(self.on_mnuBar)     # Connexions des routines du menu application
    self.ui.mnuAppOuvrir.triggered.connect(self.on_mnuAppOuvrir)
    self.ui.mnuAppEnregistrer.triggered.connect(self.on_mnuAppEnregistrer)
    self.ui.mnuAppEnregistrerSous.triggered.connect(self.on_mnuAppEnregistrerSous)
    self.ui.mnuAppFermerGCode.triggered.connect(self.on_mnuAppFermerGCode)
    self.ui.mnuAppQuitter.triggered.connect(self.on_mnuAppQuitter)

    self.ui.mnu_GrblConfig.triggered.connect(self.on_mnu_GrblConfig)
    self.ui.mnu_MPos.triggered.connect(self.on_mnu_MPos)
    self.ui.mnu_WPos.triggered.connect(self.on_mnu_WPos)
    self.ui.mnuDebug_mode.triggered.connect(self.on_mnuDebug_mode)

    self.ui.btnRefresh.clicked.connect(self.populatePortList)            # Refresh de la liste des ports serie
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)           # un clic sur le bouton "(De)Connecter" appellera la méthode 'action_btnConnect'
    self.ui.btnSend.pressed.connect(self.sendCmd)                        # Bouton d'envoi de commandes unitaires
    self.ui.txtGCode.returnPressed.connect(self.sendCmd)                 # Même fonction par la touche entrée
    self.ui.txtGCode.textChanged.connect(self.txtGCode_on_Change)        # Analyse du champ de saisie au fur et a mesure de son édition
    self.ui.txtGCode.keyPressed.connect(self.on_keyPressed)
    ###self.ui.btnStartTimer.clicked.connect(self.startTimer)
    ###self.ui.btnStopTimer.clicked.connect(self.stopTimer)
    self.ui.btnDebug.clicked.connect(self.on_btnDebug)
    self.ui.btnPausePooling.clicked.connect(self.on_btnPausePooling)

    self.ui.btnClearDebug.clicked.connect(self.clearDebug)
    self.ui.btnSpinM3.clicked.connect(self.on_btnSpinM3)
    self.ui.btnSpinM4.clicked.connect(self.on_btnSpinM4)
    self.ui.btnSpinM5.clicked.connect(self.on_btnSpinM5)
    self.ui.btnFloodM7.clicked.connect(self.on_btnFloodM7)
    self.ui.btnFloodM8.clicked.connect(self.on_btnFloodM8)
    self.ui.btnFloodM9.clicked.connect(self.on_btnFloodM9)
    self.ui.lblG54.clicked.connect(self.on_lblG5xClick)
    self.ui.lblG55.clicked.connect(self.on_lblG5xClick)
    self.ui.lblG56.clicked.connect(self.on_lblG5xClick)
    self.ui.lblG57.clicked.connect(self.on_lblG5xClick)
    self.ui.lblG58.clicked.connect(self.on_lblG5xClick)
    self.ui.lblG59.clicked.connect(self.on_lblG5xClick)
    self.ui.btnJogMoinsX.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusX.mousePress.connect(self.on_jog)
    self.ui.btnJogMoinsY.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusY.mousePress.connect(self.on_jog)
    self.ui.btnJogMoinsZ.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusZ.mousePress.connect(self.on_jog)
    self.ui.btnJogMoinsA.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusA.mousePress.connect(self.on_jog)
    self.ui.btnJogMoinsB.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusB.mousePress.connect(self.on_jog)
    self.ui.btnJogStop.mousePress.connect(self.__jog.jogCancel)
    self.ui.rbRapid025.clicked.connect(lambda: self.__grblCom.realTimePush(REAL_TIME_RAPID_25_POURCENT))
    self.ui.rbRapid050.clicked.connect(lambda: self.__grblCom.realTimePush(REAL_TIME_RAPID_50_POURCENT))
    self.ui.rbRapid100.clicked.connect(lambda: self.__grblCom.realTimePush(REAL_TIME_RAPID_100_POURCENT))
    self.ui.dialAvance.valueChanged.connect(self.on_feedOverride)
    self.ui.dialBroche.valueChanged.connect(self.on_spindleOverride)
    self.ui.btnLinkOverride.clicked.connect(self.on_btnLinkOverride)
    self.ui.btnResetAvance.clicked.connect(self.on_btnResetAvance)
    self.ui.btnResetBroche.clicked.connect(self.on_btnResetBroche)
    self.ui.btnKillAlarm.clicked.connect(self.on_btnKillAlarm)
    self.ui.btnHomeCycle.clicked.connect(self.on_btnHomeCycle)
    self.ui.btnReset.clicked.connect(self.on_btnReset)
    self.ui.btnStart.clicked.connect(self.startCycle)
    self.ui.btnPause.clicked.connect(self.pauseCycle)
    self.ui.btnStop.clicked.connect(self.stopCycle)
    self.ui.gcodeTable.customContextMenuRequested.connect(self.on_gcodeTableContextMenu)
    self.ui.dialAvance.customContextMenuRequested.connect(self.on_dialAvanceContextMenu)
    self.ui.dialBroche.customContextMenuRequested.connect(self.on_dialBrocheContextMenu)
    self.ui.lblLblPosX.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("X"))
    self.ui.lblLblPosY.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("Y"))
    self.ui.lblLblPosZ.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("Z"))
    self.ui.lblLblPosA.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("A"))
    self.ui.lblLblPosB.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("B"))
    #self.ui.lblLblPosC.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("C"))
    self.ui.lblPosX.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("X"))
    self.ui.lblPosY.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("Y"))
    self.ui.lblPosZ.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("Z"))
    self.ui.lblPosA.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("A"))
    self.ui.lblPosB.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("B"))
    #self.ui.lblPosC.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu("C"))
    self.ui.lblPlan.customContextMenuRequested.connect(self.on_lblPlanContextMenu)
    self.ui.lblUnites.customContextMenuRequested.connect(self.on_lblUnitesContextMenu)
    self.ui.lblCoord.customContextMenuRequested.connect(self.on_lblCoordContextMenu)

    #--------------------------------------------------------------------------------------
    # Traitement des arguments de la ligne de commande
    #--------------------------------------------------------------------------------------
    if self.__args.connect:
      # Connection du port série
      self.action_btnConnect()

    if self.__args.file != None:
      # Charge le fichier GCode a l'ouverture
      # Curseur sablier
      self.setCursor(Qt.WaitCursor)
      RC = self.__gcodeFile.readFile(self.__args.file)
      if RC:
        # Sélectionne l'onglet du fichier
        self.ui.grpConsole.setCurrentIndex(1)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.filePath())
      else:
        # Sélectionne l'onglet de la console pour que le message d'erreur s'affiche
        self.ui.grpConsole.setCurrentIndex(2)
      # Restore le curseur de souris
      self.setCursor(Qt.ArrowCursor)

    if self.__args.noUrgentStop:
      self.__arretUrgence = False
      self.log(logSeverity.info.value, "Arrêt d'urgence déverrouillé.")

    # Initialise l'état d'activation ou non des contrôles
    # En fonction de la sélection du port série ou non
    self.setEnableDisableConnectControls()
    # Active ou désactive les boutons de cycle
    self.setEnableDisableGroupes()

  def populatePortList(self):
    ''' Rempli la liste des ports série '''
    self.ui.cmbPort.clear()
    self.ui.cmbPort.addItem("")
    if len(QSerialPortInfo.availablePorts()) > 0:
      for p in QSerialPortInfo.availablePorts():
        self.ui.cmbPort.addItem(p.portName() + ' - ' + p.description())
        if self.__args.port != None:
          if self.__args.port == p.portName() or self.__args.port == p.systemLocation():
            self.ui.cmbPort.setCurrentIndex(len(self.ui.cmbPort)-1)
    else:
      m = msgBox(
                  title  = "Attention !",
                  text   = "Aucun port de communication disponible !",
                  info   = sys.argv[0] + " n'a pas trouvé de port série permettant de communiquer avec grbl.",
                  icon   = msgIconList.Information,
                  detail = "\nclass serialCom:\nL'appel de \"serial.tools.list_ports.comports()\" n'a renvoyé aucun port.",
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
    # S'il n'y a qu'un seul port série et que l'on a rien précisé comme option port, on le sélectionne
    if self.__args.port == None:
      if len(QSerialPortInfo.availablePorts()) == 1:
        self.ui.cmbPort.setCurrentIndex(1)
    # Définit l'activation des contrôles en fonction de la sélection du port série ou non
    self.setEnableDisableConnectControls()


  def setEnableDisableConnectControls(self):
    '''
    Active ou désactive les contrôles de connexion en fonction de
    l'état de connection et de sélection du port
    '''
    if self.__connectionStatus:
      self.ui.cmbPort.setEnabled(False)
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setEnabled(True)
    else:
      self.ui.cmbPort.setEnabled(True)
      if self.ui.cmbPort.currentText() == "":
        self.ui.cmbBauds.setEnabled(False)
        self.ui.btnConnect.setEnabled(False)
      else:
        self.ui.cmbBauds.setEnabled(True)
        self.ui.btnConnect.setEnabled(True)


  def setEnableDisableGroupes(self):
    '''
    Détermine l'état Enable/Disable des différents groupes de contrôles
    en fonction de l'état de connexion et de l'état du bouton d'arrêt d'urgence.
    '''
    if not self.__connectionStatus:
      # Pas connecté, tout doit être désactivé et l'arrêt d'urgence enfoncé
      self.ui.btnUrgence.setIcon(QtGui.QIcon(':/cn5X/images/btnUrgenceOff.svg'))
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(False)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      ###self.ui.frmCoordOffsets.setEnabled(False)
      self.ui.grpStatus.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    elif self.__arretUrgence:
      # Connecté mais sous arrêt d'urgence : Tout est désactivé sauf l'arrêt d'urgence
      self.ui.btnUrgence.setIcon(QtGui.QIcon(':/cn5X/images/btnUrgenceOff.svg'))
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      ###self.ui.frmCoordOffsets.setEnabled(False)
      self.ui.grpStatus.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    else:
      # Tout est en ordre, on active tout
      self.ui.btnUrgence.setIcon(QtGui.QIcon(':/cn5X/images/btnUrgence.svg'))
      self.ui.btnUrgence.setToolTip("Arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(True)
      self.ui.grpJog.setEnabled(True)
      self.ui.frmGcodeInput.setEnabled(True)
      self.ui.frmBoutons.setEnabled(True)
      ###self.ui.frmCoordOffsets.setEnabled(True)
      self.ui.grpStatus.setEnabled(True)
      self.ui.frmHomeAlarm.setEnabled(True)
      if self.__gcodeFile.isFileLoaded():
        self.ui.frmCycle.setEnabled(True)
      else:
        self.ui.frmCycle.setEnabled(False)


  @pyqtSlot()
  def on_mnuBar(self):
    if self.__gcodeFile.isFileLoaded():
      self.ui.mnuAppEnregistrerSous.setEnabled(True)
      self.ui.mnuAppFermerGCode.setEnabled(True)
      if self.__gcodeFile.gcodeChanged():
        self.ui.mnuAppEnregistrer.setEnabled(True)
      else:
        self.ui.mnuAppEnregistrer.setEnabled(False)
    else:
      self.ui.mnuAppEnregistrer.setEnabled(False)
      self.ui.mnuAppEnregistrerSous.setEnabled(False)
      self.ui.mnuAppFermerGCode.setEnabled(False)
    if self.__connectionStatus:
      self.ui.mnu_MPos.setEnabled(True)
      self.ui.mnu_WPos.setEnabled(True)
      if self.__arretUrgence:
        self.ui.mnu_GrblConfig.setEnabled(True)
      else:
        self.ui.mnu_GrblConfig.setEnabled(False)
    else:
      self.ui.mnu_MPos.setEnabled(False)
      self.ui.mnu_WPos.setEnabled(False)
      self.ui.mnu_GrblConfig.setEnabled(False)


  @pyqtSlot()
  def on_mnuAppOuvrir(self):
    # Affiche la boite de dialogue d'ouverture
    fileName = self.__gcodeFile.showFileOpen()
    if fileName[0] != "":
      # Lecture du fichier
      # Curseur sablier
      self.setCursor(Qt.WaitCursor)
      RC = self.__gcodeFile.readFile(fileName[0])
      if RC:
        # Sélectionne l'onglet du fichier
        self.ui.grpConsole.setCurrentIndex(1)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.filePath())
      else:
        # Sélectionne l'onglet de la console pour que le message d'erreur s'affiche
        self.ui.grpConsole.setCurrentIndex(2)
    # Active ou désactive les boutons de cycle
    self.setEnableDisableGroupes()
    # Restore le curseur de souris
    self.setCursor(Qt.ArrowCursor)


  @pyqtSlot()
  def on_mnuAppEnregistrer(self):
    if self.__gcodeFile.filePath != "":
      self.__gcodeFile.saveFile()


  @pyqtSlot()
  def on_mnuAppEnregistrerSous(self):
    self.__gcodeFile.saveAs()


  @pyqtSlot()
  def on_mnuAppFermerGCode(self):
    self.__gcodeFile.closeFile()


  @pyqtSlot()
  def on_mnuAppQuitter(self):
    self.close()


  def closeEvent(self, event):
    self.log(logSeverity.info.value, "Close event...")
    if self.__connectionStatus:
      self.__grblCom.stopCom()
    if not self.__gcodeFile.closeFile():
      self.log(logSeverity.info.value, "Fermeture du fichier annulée")
      event.setAccepted(False)
    else:
      self.__statusText = "Bye-bye..."
      self.ui.statusBar.showMessage(self.__statusText)
      event.accept() # let the window close
    ###event.setAccepted(False) # True accepte la fermeture, False annule la fermeture


  @pyqtSlot()
  def on_mnu_MPos(self):
    if self.ui.mnu_MPos.isChecked():
      param10 = 255 # Le bit 1 est à 1
      self.__grblCom.gcodeInsert("$10=" + str(param10))


  @pyqtSlot()
  def on_mnu_WPos(self):
    if self.ui.mnu_WPos.isChecked():
      param10 = 255 ^ 1 # Met le bit 1 à 0
      self.__grblCom.gcodeInsert("$10=" + str(param10))


  @pyqtSlot()
  def on_mnu_GrblConfig(self):
    ''' Appel de la boite de dialogue de configuration
    '''
    self.__grblConfigLoaded = True
    dlgConfig = grblConfig(self.__grblCom)
    dlgConfig.showDialog()
    self.__grblConfigLoaded = False


  @pyqtSlot()
  def on_arretUrgence(self):
    if self.__arretUrgence:
      # L'arrêt d'urgence est actif, on doit faire un double click pour le désactiver
      if not self.timerDblClic.isActive():
        # On est pas dans le timer du double click,
        # c'est donc un simple click qui ne suffit pas à déverrouiller le bouton d'arrêt d'urgence,
        # C'est le premier click, On active le timer pour voir le le 2ème sera dans le temp imparti
        self.timerDblClic.setSingleShot(True)
        self.timerDblClic.start(QtWidgets.QApplication.instance().doubleClickInterval())
      else:
        # self.timerDblClic.remainingTime() > 0 # Double clic détecté
        self.timerDblClic.stop()
        self.__arretUrgence = False
        self.log(logSeverity.info.value, "Déverouillage de l'arrêt d'urgence.")
    else:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
      self.__arretUrgence = True
      self.log(logSeverity.warning.value, "Arrêt d'urgence STOP !!!")

    # Actualise l'état actif/inactif des groupes de contrôles de pilotage de Grbl
    self.setEnableDisableGroupes()


  @pyqtSlot()
  def action_btnConnect(self):
    if self.ui.btnConnect.text() != "":
      if self.ui.btnConnect.text() == "Connecter":
        # Force l'onglet "Grbl output"
        self.ui.grpConsole.setCurrentIndex(0)
        # Recupère les coordonnées et paramètres du port à connecter
        serialDevice = self.ui.cmbPort.currentText()
        serialDevice = serialDevice.split("-")
        serialDevice = serialDevice[0].strip()
        baudRate = int(self.ui.cmbBauds.currentText())
        # Démarrage du communicator
        self.__grblCom.startCom(serialDevice, baudRate)
      else:
        # Arret du comunicator
        self.__grblCom.stopCom()


  @pyqtSlot()
  def on_sig_connect(self):
    self.__connectionStatus = self.__grblCom.isOpen()
    if self.__connectionStatus:
      # Mise à jour de l'interface
      self.ui.lblConnectStatus.setText("Connecté à " + self.ui.cmbPort.currentText().split("-")[0].strip())
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
      self.setEnableDisableConnectControls()
      # Active les groupes de contrôles de pilotage de Grbl
      self.setEnableDisableGroupes()
    else:
      # Mise à jour de l'interface
      self.ui.lblConnectStatus.setText("<Non Connecté>")
      self.ui.btnConnect.setText("Connecter") # La prochaine action du bouton sera pour connecter
      self.__statusText = ""
      self.ui.statusBar.showMessage(self.__statusText)
      self.setEnableDisableConnectControls()
      # Force la position de l'arrêt d'urgence
      self.__arretUrgence = True
      # Active les groupes de contrôles de pilotage de Grbl
      self.setEnableDisableGroupes()


  @pyqtSlot(int)
  def on_feedOverride(self, value: int):
    adjustFeedOverride(int(self.ui.lblAvancePourcent.text()[:-1]), value, self.__grblCom)
    self.ui.lblAvancePourcent.setText("{}%".format(value))
    if self.ui.btnLinkOverride.isChecked() and (value != self.ui.dialBroche.value()):
      self.ui.dialBroche.setValue(value)


  @pyqtSlot(int)
  def on_spindleOverride(self, value: int):
    adjustSpindleOverride(int(self.ui.lblBrochePourcent.text()[:-1]), value, self.__grblCom)
    self.ui.lblBrochePourcent.setText("{}%".format(value))
    if self.ui.btnLinkOverride.isChecked() and (value != self.ui.dialAvance.value()):
      self.ui.dialAvance.setValue(value)


  @pyqtSlot()
  def on_btnLinkOverride(self):
    if self.ui.btnLinkOverride.isChecked() and (self.ui.dialAvance.value() != self.ui.dialBroche.value()):
      newValue = (self.ui.dialAvance.value() + self.ui.dialBroche.value()) / 2
      self.ui.dialBroche.setValue(newValue)
      self.ui.dialAvance.setValue(newValue)


  @pyqtSlot()
  def on_btnResetAvance(self):
    self.ui.dialAvance.setValue(100)


  @pyqtSlot()
  def on_btnResetBroche(self):
    self.ui.dialBroche.setValue(100)


  @pyqtSlot()
  def on_cmbPort_changed(self):
    self.setEnableDisableConnectControls()


  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent)
  def on_jog(self, cnButton, e):
    jogDistance = 0
    for qrb in [self.ui.rbtJog0000, self.ui.rbtJog0001, self.ui.rbtJog0010, self.ui.rbtJog0100, self.ui.rbtJog1000]:
      if qrb.isChecked():
        jogDistance = float(qrb.text().replace(' ', ''))
    self.__jog.on_jog(cnButton, e, jogDistance)


  @pyqtSlot()
  def on_btnSpinM3(self):
    ###self.logGrbl.append("M3")
    self.__grblCom.gcodeInsert("M3")
    self.ui.btnSpinM4.setEnabled(False) # Interdit un changement de sens de rotation direct


  @pyqtSlot()
  def on_btnSpinM4(self):
    ###self.logGrbl.append("M4")
    self.__grblCom.gcodeInsert("M4")
    self.ui.btnSpinM3.setEnabled(False) # Interdit un changement de sens de rotation direct


  @pyqtSlot()
  def on_btnSpinM5(self):
    ###self.logGrbl.append("M5")
    self.__grblCom.gcodeInsert("M5")
    self.ui.btnSpinM3.setEnabled(True)
    self.ui.btnSpinM4.setEnabled(True)


  @pyqtSlot()
  def on_btnFloodM7(self):
    if self.decode.get_etatArrosage() != "M7" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M7")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)


  @pyqtSlot()
  def on_btnFloodM8(self):
    if self.decode.get_etatArrosage() != "M8" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M8")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot()
  def on_btnFloodM9(self):
    if self.decode.get_etatArrosage() == "M7" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)
    if self.decode.get_etatArrosage() == "M8" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M9")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot(str, QtGui.QMouseEvent)
  def on_lblG5xClick(self, lblText, e):
    ###self.logGrbl.append(lblText)
    self.__grblCom.gcodeInsert(lblText)


  @pyqtSlot()
  def on_btnKillAlarm(self):
    ###self.logGrbl.append(CMD_GRBL_KILL_ALARM_LOCK)
    self.__grblCom.gcodeInsert(CMD_GRBL_KILL_ALARM_LOCK)


  @pyqtSlot()
  def on_btnHomeCycle(self):
    ###self.logGrbl.append(CMD_GRBL_RUN_HOME_CYCLE)
    self.__grblCom.gcodeInsert(CMD_GRBL_RUN_HOME_CYCLE)


  @pyqtSlot()
  def on_btnReset(self):
    self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET)


  @pyqtSlot()
  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      if self.ui.txtGCode.text() == REAL_TIME_REPORT_QUERY:
        self.decode.getNextStatus()
    self.__grblCom.gcodePush(self.ui.txtGCode.text())
    self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
    self.ui.txtGCode.setFocus()


  @pyqtSlot()
  def txtGCode_on_Change(self):
    if self.ui.txtGCode.text() == REAL_TIME_REPORT_QUERY:
      self.logGrbl.append(REAL_TIME_REPORT_QUERY)
      self.decode.getNextStatus()
      self.__grblCom.realTimePush(REAL_TIME_REPORT_QUERY) # Envoi direct ? sans attendre le retour chariot.
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))


  @pyqtSlot(QtGui.QKeyEvent)
  def on_keyPressed(self, e):
    if QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+C"):
      pass
    elif QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+X"):
      self.logGrbl.append("Ctrl+X")
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.


  @pyqtSlot(int, str)
  def on_sig_log(self, severity: int, data: str):
    if severity == logSeverity.info.value:
      self.logCn5X.setTextColor(TXT_COLOR_GREEN)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Info    : " + data)
    elif severity == logSeverity.warning.value:
      self.logCn5X.setTextColor(TXT_COLOR_ORANGE)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Warning : " + data)
      self.ui.grpConsole.setCurrentIndex(2)
    elif severity == logSeverity.error.value:
      self.logCn5X.setTextColor(TXT_COLOR_RED)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Error   : " + data)
      self.ui.grpConsole.setCurrentIndex(2)
  def log(self, severity: int, data: str):
    self.on_sig_log(severity, data)

  @pyqtSlot(str)
  def on_sig_init(self, data: str):
    self.log(logSeverity.info.value, "cn5X++ : Grbl initialisé.")
    self.logGrbl.append(data)
    self.__statusText = data.split("[")[0]
    self.ui.statusBar.showMessage(self.__statusText)
    self.__grblCom.gcodeInsert("\n")


  @pyqtSlot()
  def on_sig_ok(self):
    self.logGrbl.append("ok")


  @pyqtSlot(int)
  def on_sig_error(self, errNum: int):
    self.logGrbl.append(self.decode.errorMessage(errNum))


  @pyqtSlot(int)
  def on_sig_alarm(self, alarmNum: int):
    self.logGrbl.append(self.decode.alarmMessage(alarmNum))


  @pyqtSlot(str)
  def on_sig_status(self, data: str):
    retour = self.decode.decodeGrblStatus(data)
    if retour != "":
      self.logGrbl.append(retour)


  @pyqtSlot(str)
  def on_sig_data(self, data: str):
    retour = self.decode.decodeGrblData(data)
    if retour is not None and retour != "":
      self.logGrbl.append(retour)


  @pyqtSlot(str)
  def on_sig_config(self, data: str):
    # Repère la chaine "[AXS:5:XYZAB]" pour récupérer le nombre d'axes et leurs noms
    if data[:5] == "[AXS:":
      print(data[1:-1])
      self.__nbAxis           = data[1:-1].split(':')[1]
      print(self.__nbAxis)
      self.__axisNames        = list(data[1:-1].split(':')[2])
      print(self.__axisNames)

    if not self.__grblConfigLoaded:
      self.logGrbl.append(data)


  @pyqtSlot(str)
  def on_sig_emit(self, data: str):
    if data != "":
      self.logGrbl.append(data)
      if self.__cycleRun:
        # Recherche la ligne dans la liste du fichier GCode
        ligne = self.__gcodeFile.getGCodeSelectedLine()[0]
        while ligne < self.ui.gcodeTable.model().rowCount():
          idx = self.ui.gcodeTable.model().index(ligne, 0, QModelIndex())
          if self.ui.gcodeTable.model().data(idx) == data:
            self.__gcodeFile.selectGCodeFileLine(ligne)
            break
          else:
            ligne += 1


  @pyqtSlot(str)
  def on_sig_recu(self, data: str):
    pass


  @pyqtSlot(str)
  def on_sig_debug(self, data: str):
    if self.ui.mnuDebug_mode.isChecked():
      self.logDebug.append(data)


  @pyqtSlot()
  def on_mnuDebug_mode(self):
    ''' Set the debug button on the same status '''
    if self.ui.mnuDebug_mode.isChecked():
      if not self.ui.btnDebug.isChecked():
        self.ui.btnDebug.setChecked(True)
      self.ui.btnPausePooling.setEnabled(True)
    else:
      if self.ui.btnDebug.isChecked():
        self.ui.btnDebug.setChecked(False)
      # Ensure pooling in active when debug is off
      self.ui.btnPausePooling.setEnabled(False)
      self.ui.btnPausePooling.setChecked(False)
      self.__grblCom.startPooling()


  @pyqtSlot()
  def on_btnDebug(self):
    ''' Set the debug menu on the same status '''
    if self.ui.btnDebug.isChecked():
      if not self.ui.mnuDebug_mode.isChecked():
        self.ui.mnuDebug_mode.setChecked(True)
      self.ui.btnPausePooling.setEnabled(True)
    else:
      if self.ui.mnuDebug_mode.isChecked():
        self.ui.mnuDebug_mode.setChecked(False)
      # Ensure pooling in active when debug is off
      self.ui.btnPausePooling.setEnabled(False)
      self.ui.btnPausePooling.setChecked(False)
      self.__grblCom.startPooling()


  @pyqtSlot()
  def on_btnPausePooling(self):
    print("on_btnPausePooling()")
    if self.ui.btnPausePooling.isChecked():
      self.__grblCom.stopPooling()
    else:
      self.__grblCom.startPooling()


  @pyqtSlot()
  def clearDebug(self):
    self.logDebug.clear()


  def startCycle(self):
    self.log(logSeverity.info.value, "Démarrage du cycle...")
    self.__gcodeFile.selectGCodeFileLine(0)
    self.__cycleRun = True
    self.__cyclePause = False
    self.__gcodeFile.enQueue(self.__grblCom)
    self.ui.btnStart.setButtonStatus(True)
    self.ui.btnPause.setButtonStatus(False)
    self.ui.btnStop.setButtonStatus(False)


  def pauseCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      self.log(logSeverity.warning.value, "Hold en cours, impossible de repartir maintenant.")
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      self.log(logSeverity.info.value, "Reprise du cycle...")
      self.__grblCom.realTimePush(REAL_TIME_CYCLE_START_RESUME)
      self.__cyclePause = False
      self.ui.btnStart.setButtonStatus(True)
      self.ui.btnPause.setButtonStatus(False)
      self.ui.btnStop.setButtonStatus(False)
    else:
      self.log(logSeverity.info.value, "Pause du cycle...")
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      self.__cyclePause = True
      self.ui.btnStart.setButtonStatus(False)
      self.ui.btnPause.setButtonStatus(True)
      self.ui.btnStop.setButtonStatus(False)


  def stopCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      # Déja en pause, on vide la file d'attente et on envoie un SoftReset
      self.log(logSeverity.info.value, "Arrêt du cycle...")
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    elif self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      # Attente que le Hold soit terminé
      self.log(logSeverity.info.value, "Pause en cours avant arrêt du cycle...")
      while self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, "Arrêt du cycle...")
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    else:
      # Envoie une pause
      self.log(logSeverity.info.value, "Pause avant arrêt du cycle...")
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      # Attente que le Hold soit terminé
      while self.ui.lblEtat.text() != GRBL_STATUS_HOLD0:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, "Arrêt du cycle...")
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    self.__cycleRun = False
    self.__cyclePause = False
    self.ui.btnStart.setButtonStatus(False)
    self.ui.btnPause.setButtonStatus(False)
    self.ui.btnStop.setButtonStatus(True)
    self.log(logSeverity.info.value, "Cycle terminé.")


  def on_gcodeTableContextMenu(self, event):
    if self.__gcodeFile.isFileLoaded():
      self.cMenu = QtWidgets.QMenu(self)
      editAction = QtWidgets.QAction('Editer la ligne', self)
      editAction.triggered.connect(lambda: self.editGCodeSlot(event))
      self.cMenu.addAction(editAction)
      insertAction = QtWidgets.QAction('Insérer une ligne', self)
      insertAction.triggered.connect(lambda: self.insertGCodeSlot(event))
      self.cMenu.addAction(insertAction)
      ajoutAction = QtWidgets.QAction('Ajouter une ligne', self)
      ajoutAction.triggered.connect(lambda: self.ajoutGCodeSlot(event))
      self.cMenu.addAction(ajoutAction)
      supprimeAction = QtWidgets.QAction('Supprimer la ligne', self)
      supprimeAction.triggered.connect(lambda: self.supprimeGCodeSlot(event))
      self.cMenu.addAction(supprimeAction)
      self.cMenu.popup(QtGui.QCursor.pos())

  def editGCodeSlot(self, event):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.ui.gcodeTable.edit(idx[0])

  def insertGCodeSlot(self, event):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.__gcodeFile.insertGCodeFileLine(idx[0].row())
    self.__gcodeFile.selectGCodeFileLine(idx[0].row())
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.ui.gcodeTable.edit(idx[0])

  def ajoutGCodeSlot(self, event):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.__gcodeFile.addGCodeFileLine(idx[0].row())
    self.__gcodeFile.selectGCodeFileLine(idx[0].row()+1)
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.ui.gcodeTable.edit(idx[0])

  def supprimeGCodeSlot(self, event):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.__gcodeFile.deleteGCodeFileLine(idx[0].row())


  def on_dialAvanceContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    resetAction = QtWidgets.QAction("Réinitialiser l'avance à 100%", self)
    resetAction.triggered.connect(lambda: self.ui.dialAvance.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_dialBrocheContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    resetAction = QtWidgets.QAction("Réinitialiser la vitesse de broche à 100%", self)
    resetAction.triggered.connect(lambda: self.ui.dialBroche.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblPosContextMenu(self, axis: str):
    self.cMenu = QtWidgets.QMenu(self)
    resetX = QtWidgets.QAction("Réinitialiser l'axe {} à zéro".format(axis), self)
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush("G10 P0 L20 {}0".format(axis)))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction("Réinitialiser tous les axes à zéro", self)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush("G10 P0 L20 X0 Y0 Z0 A0 B0"))
    self.cMenu.addAction(resetAll)
    self.cMenu.addSeparator()
    resetX = QtWidgets.QAction("Retour de {} à la position zéro".format(axis), self)
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush("G90 G0 {}0".format(axis)))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction("Retour de tous les axes en position zéro", self)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush("G90 G0 X0 Y0 Z0 A0 B0"))
    self.cMenu.addAction(resetAll)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblPlanContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    planXY = QtWidgets.QAction("Plan de travail G17 - XY (Défaut)", self)
    planXY.triggered.connect(lambda: self.__grblCom.gcodePush("G17"))
    self.cMenu.addAction(planXY)
    planXZ = QtWidgets.QAction("Plan de travail G18 - XZ", self)
    planXZ.triggered.connect(lambda: self.__grblCom.gcodePush("G18"))
    self.cMenu.addAction(planXZ)
    planYZ = QtWidgets.QAction("Plan de travail G19 - YZ", self)
    planYZ.triggered.connect(lambda: self.__grblCom.gcodePush("G19"))
    self.cMenu.addAction(planYZ)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblUnitesContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction("G20 - Unités travail en pouces", self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G20"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction("G21 - Unités travail en millimètres", self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G21"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblCoordContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction("G90 - Déplacements en coordonnées absolues", self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G90"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction("G91 - Déplacements en coordonnées relatives", self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G91"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


"""******************************************************************"""


if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
