#! /usr/bin/env python3
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
import sys, os, time
import argparse
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, QThread, pyqtSignal, pyqtSlot, QModelIndex,  QItemSelectionModel, QFileInfo, QTranslator, QLocale, QSettings
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem, QValidator
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
from cn5Xapropos import cn5XAPropos
from xml.dom.minidom import parse, Node, Element

class upperCaseValidator(QValidator):
  def validate(self, string, pos):
    return QValidator.Acceptable, string.upper(), pos

import mainWindow

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)

    self.ucase = upperCaseValidator(self)
    self.__gcodes_stack = []
    self.__gcodes_stack_pos = -1
    self.__gcode_recall_flag = False
    self.__gcode_current_txt = ""

    self.settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)

    ###print("Demarrage de {}.{}.".format(self.settings.organizationName(), self.settings.applicationName()))
    ###print("Liste des settings = *{}*".format(self.settings.allKeys()))
    ###print("Lang settings = *{}*".format(self.settings.value("lang", "default")))

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--connect", action="store_true", help=self.tr("Connecte le port serie"))
    parser.add_argument("-f", "--file", help=self.tr("Charge le fichier GCode"))
    parser.add_argument("-l", "--lang", help=self.tr("Definie la langue de l'interface"))
    parser.add_argument("-p", "--port", help=self.tr("selection du port serie"))
    parser.add_argument("-u", "--noUrgentStop", action="store_true", help=self.tr("Deverrouille l'arret d'urgence"))
    self.__args = parser.parse_args()

    # Retrouve le fichier de licence dans le même répertoire que l'exécutable
    if getattr(sys, 'frozen', False):
        # frozen
        dir_ = os.path.dirname(sys.executable)
    else:
        # unfrozen
        dir_ = os.path.dirname(os.path.realpath(__file__))
    self.__licenceFile = "{}/COPYING".format(dir_)

    # Initialise la fenêtre princpale
    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)

    self.btnUrgencePictureLocale = ":/cn5X/images/btnUrgence.svg"
    self.btnUrgenceOffPictureLocale = ":/cn5X/images/btnUrgenceOff.svg"

    # création du menu des langues
    self.createLangMenu()

    self.logGrbl  = self.ui.txtGrblOutput    # Tous les messages de Grbl seront rediriges dans le widget txtGrblOutput
    self.logCn5X  = self.ui.txtConsoleOutput # Tous les messages applicatif seront rediriges dans le widget txtConsoleOutput
    self.logDebug = self.ui.txtDebugOutput   # Message debug de Grbl

    self.logGrbl.document().setMaximumBlockCount(2000)  # Limite la taille des logs a 2000 lignes
    self.logCn5X.document().setMaximumBlockCount(2000)  # Limite la taille des logs a 2000 lignes
    self.logDebug.document().setMaximumBlockCount(2000) # Limite la taille des logs a 2000 lignes
    self.ui.grpConsole.setCurrentIndex(2)               # Active le tab de la log cn5X++

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
    self.ui.dsbJogSpeed.setValue(DEFAULT_JOG_SPEED)
    self.ui.dsbJogSpeed.valueChanged.connect(self.on_dsbJogSpeed_valueChanged)

    self.__connectionStatus = False
    self.__arretUrgence     = True
    self.__cycleRun         = False
    self.__cyclePause       = False
    self.__grblConfigLoaded = False
    self.__nbAxis           = DEFAULT_NB_AXIS
    self.__axisNames        = DEFAULT_AXIS_NAMES
    self.updateAxisNumber()

    ###pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    ###os.chdir(pathname)

    """---------- Preparation de l'interface ----------"""

    # On traite la langue.
    if self.__args.lang != None:
      # l'argument sur la ligne de commande est prioritaire.
      #print("Locale demandee : {}".format(self.__args.lang))
      locale = QLocale(self.__args.lang)
    else:
      # Si une langue est définie dans les settings, on l'applique
      settingsLang = self.settings.value("lang", "default")
      if settingsLang != "default":
        locale = QLocale(settingsLang)
      else:
        # On prend la locale du système par défaut
        locale = QLocale()

    self.setTranslator(locale)

    QtGui.QFontDatabase.addApplicationFont(":/cn5X/fonts/LEDCalculator.ttf")  # Police type "LED"
    self.ui.btnConnect.setText(self.tr("Connecter"))                          # Label du bouton connect
    self.populatePortList()                                                   # On rempli la liste des ports serie

    app.setStyleSheet("QToolTip { background-color: rgb(248, 255, 192); color: rgb(0, 0, 63); }")

    curIndex = -1                                                             # On rempli la liste des vitesses
    for v in QSerialPortInfo.standardBaudRates():
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == COM_DEFAULT_BAUD_RATE:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenetre (status bar)
    self.__statusText = ""
    self.ui.statusBar.showMessage(self.__statusText)

    # Positionne l'etat d'activation des controles
    self.setEnableDisableGroupes()

    """---------- Connections des evennements de l'interface graphique ----------"""
    self.ui.btnUrgence.pressed.connect(self.on_arretUrgence)             # Evenements du bouton d'arret d'urgence
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed) # un clic sur un element de la liste appellera la methode 'on_cmbPort_changed'

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

    self.ui.mnuA_propos.triggered.connect(self.on_mnuA_propos)

    self.ui.btnRefresh.clicked.connect(self.populatePortList)            # Refresh de la liste des ports serie
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)           # un clic sur le bouton "(De)Connecter" appellera la methode 'action_btnConnect'
    self.ui.btnSend.pressed.connect(self.sendCmd)                        # Bouton d'envoi de commandes unitaires
    self.ui.txtGCode.setValidator(self.ucase)                            # Force la saisie des GCodes en majuscules
    self.ui.txtGCode.returnPressed.connect(self.sendCmd)                 # Meme fonction par la touche entree que le bouton d'envoi
    self.ui.txtGCode.textChanged.connect(self.txtGCode_on_Change)        # Analyse du champ de saisie au fur et a mesure de son edition
    self.ui.txtGCode.keyPressed.connect(self.on_keyPressed)
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
    self.ui.btnJogMoinsC.mousePress.connect(self.on_jog)
    self.ui.btnJogPlusC.mousePress.connect(self.on_jog)
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
    self.ui.lblLblPosX.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(0))
    self.ui.lblLblPosY.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(1))
    self.ui.lblLblPosZ.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(2))
    self.ui.lblLblPosA.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(3))
    self.ui.lblLblPosB.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(4))
    self.ui.lblLblPosC.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(5))
    self.ui.lblPosX.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(0))
    self.ui.lblPosY.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(1))
    self.ui.lblPosZ.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(2))
    self.ui.lblPosA.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(3))
    self.ui.lblPosB.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(4))
    self.ui.lblPosC.customContextMenuRequested.connect(lambda: self.on_lblPosContextMenu(5))
    self.ui.lblPlan.customContextMenuRequested.connect(self.on_lblPlanContextMenu)
    self.ui.lblUnites.customContextMenuRequested.connect(self.on_lblUnitesContextMenu)
    self.ui.lblCoord.customContextMenuRequested.connect(self.on_lblCoordContextMenu)
    self.ui.lblG54.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(1))
    self.ui.lblG55.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(2))
    self.ui.lblG56.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(3))
    self.ui.lblG57.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(4))
    self.ui.lblG58.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(5))
    self.ui.lblG59.customContextMenuRequested.connect(lambda: self.on_lblGXXContextMenu(6))

    #--------------------------------------------------------------------------------------
    # Traitement des arguments de la ligne de commande
    #--------------------------------------------------------------------------------------
    if self.__args.connect:
      # Connection du port serie
      self.action_btnConnect()

    if self.__args.file != None:
      # Charge le fichier GCode a l'ouverture
      # Curseur sablier
      self.setCursor(Qt.WaitCursor)
      RC = self.__gcodeFile.readFile(self.__args.file)
      if RC:
        # Selectionne l'onglet du fichier sauf en cas de debug actif
        if not self.ui.btnDebug.isChecked():
          self.ui.grpConsole.setCurrentIndex(1)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.filePath())
      else:
        # Selectionne l'onglet de la console pour que le message d'erreur s'affiche sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.grpConsole.setCurrentIndex(2)
      # Restore le curseur de souris
      self.setCursor(Qt.ArrowCursor)

    if self.__args.noUrgentStop:
      self.__arretUrgence = False
      self.log(logSeverity.info.value, self.tr("Arret d'urgence deverrouille."))

    # Initialise l'etat d'activation ou non des controles
    # En fonction de la selection du port serie ou non
    self.setEnableDisableConnectControls()
    # Active ou desactive les boutons de cycle
    self.setEnableDisableGroupes()

  def populatePortList(self):
    ''' Rempli la liste des ports serie '''
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
                  title  = self.tr("Attention !"),
                  text   = self.tr("Aucun port de communication disponible !"),
                  info   = self.tr("{} n'a pas trouve de port serie permettant de communiquer avec grbl.").format(sys.argv[0]),
                  icon   = msgIconList.Information,
                  detail = self.tr("\nclass serialCom:\nL'appel de \"serial.tools.list_ports.comports()\" n'a renvoye aucun port."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
    # S'il n'y a qu'un seul port serie et que l'on a rien precise comme option port, on le selectionne
    if self.__args.port == None:
      if len(QSerialPortInfo.availablePorts()) == 1:
        self.ui.cmbPort.setCurrentIndex(1)
    # Definit l'activation des controles en fonction de la selection du port serie ou non
    self.setEnableDisableConnectControls()


  def setEnableDisableConnectControls(self):
    '''
    Active ou desactive les controles de connexion en fonction de
    l'etat de connection et de selection du port
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
    Determine l'etat Enable/Disable des differents groupes de controles
    en fonction de l'etat de connexion et de l'etat du bouton d'arret d'urgence.
    '''
    if not self.__connectionStatus:
      # Pas connecte, tout doit etre desactive et l'arret d'urgence enfonce
      self.ui.btnUrgence.setIcon(QtGui.QIcon(self.btnUrgenceOffPictureLocale))
      self.ui.btnUrgence.setToolTip(self.tr("Double clic pour\ndeverouiller l'arret d'urgence"))
      self.ui.frmArretUrgence.setEnabled(False)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      self.ui.grpStatus.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    elif self.__arretUrgence:
      # Connecte mais sous arret d'urgence : Tout est desactive sauf l'arret d'urgence
      self.ui.btnUrgence.setIcon(QtGui.QIcon(self.btnUrgenceOffPictureLocale))
      self.ui.btnUrgence.setToolTip(self.tr("Double clic pour\ndeverouiller l'arret d'urgence"))
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      self.ui.grpStatus.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    else:
      # Tout est en ordre, on active tout
      self.ui.btnUrgence.setIcon(QtGui.QIcon(self.btnUrgencePictureLocale))
      self.ui.btnUrgence.setToolTip(self.tr("Arret d'urgence"))
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(True)
      self.ui.grpJog.setEnabled(True)
      self.ui.frmGcodeInput.setEnabled(True)
      self.ui.frmBoutons.setEnabled(True)
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
        # Selectionne l'onglet du fichier sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.grpConsole.setCurrentIndex(1)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.filePath())
      else:
        # Selectionne l'onglet de la console pour que le message d'erreur s'affiche sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.grpConsole.setCurrentIndex(2)
    # Active ou desactive les boutons de cycle
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
    self.log(logSeverity.info.value, self.tr("Fermeture de l'application..."))
    if self.__connectionStatus:
      self.__grblCom.stopCom()
    if not self.__gcodeFile.closeFile():
      self.log(logSeverity.info.value, self.tr("Fermeture du fichier annulee"))
      event.setAccepted(False) # True accepte la fermeture, False annule la fermeture
    else:
      self.__statusText = "Bye-bye..."
      self.ui.statusBar.showMessage(self.__statusText)
      event.accept() # let the window close


  @pyqtSlot()
  def on_mnu_MPos(self):
    if self.ui.mnu_MPos.isChecked():
      param10 = 255 # Le bit 1 est a 1
      self.__grblCom.gcodeInsert("$10=" + str(param10))


  @pyqtSlot()
  def on_mnu_WPos(self):
    if self.ui.mnu_WPos.isChecked():
      param10 = 255 ^ 1 # Met le bit 1 a 0
      self.__grblCom.gcodeInsert("$10=" + str(param10))


  @pyqtSlot()
  def on_mnu_GrblConfig(self):
    ''' Appel de la boite de dialogue de configuration
    '''
    self.__grblConfigLoaded = True
    dlgConfig = grblConfig(self.__grblCom, self.__nbAxis, self.__axisNames)
    dlgConfig.setParent(self)
    dlgConfig.sig_config_changed.connect(self.on_sig_config_changed)
    dlgConfig.showDialog()
    self.__grblConfigLoaded = False


  @pyqtSlot(str)
  def on_sig_config_changed(self, data: str):
    self.log(logSeverity.info.value, self.tr("Configuration de Grbl changee : {}").format(data))


  @pyqtSlot()
  def on_arretUrgence(self):
    if self.__arretUrgence:
      # L'arret d'urgence est actif, on doit faire un double click pour le desactiver
      if not self.timerDblClic.isActive():
        # On est pas dans le timer du double click,
        # c'est donc un simple click qui ne suffit pas a deverrouiller le bouton d'arret d'urgence,
        # C'est le premier click, On active le timer pour voir si le 2eme sera dans le temp imparti
        self.timerDblClic.setSingleShot(True)
        self.timerDblClic.start(QtWidgets.QApplication.instance().doubleClickInterval())
      else:
        # self.timerDblClic.remainingTime() > 0 # Double clic detecte
        self.timerDblClic.stop()
        self.__arretUrgence = False
        self.log(logSeverity.info.value, self.tr("Deverouillage de l'arret d'urgence."))
    else:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
      self.__arretUrgence = True
      self.log(logSeverity.warning.value, self.tr("Arret d'urgence STOP !!!"))

    # Actualise l'etat actif/inactif des groupes de controles de pilotage de Grbl
    self.setEnableDisableGroupes()


  @pyqtSlot()
  def action_btnConnect(self):
    if not self.__connectionStatus:
      # Force l'onglet "Grbl output" sauf en cas de debug
      if not self.ui.btnDebug.isChecked():
        self.ui.grpConsole.setCurrentIndex(0)
      # Recupere les coordonnees et parametres du port a connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      baudRate = int(self.ui.cmbBauds.currentText())
      # Demarrage du communicator
      self.__grblCom.startCom(serialDevice, baudRate)
    else:
      # Arret du comunicator
      self.__grblCom.stopCom()
      self.__connectionStatus = self.__grblCom.isOpen()
      self.ui.btnConnect.setText(self.tr("Connecter")) # La prochaine action du bouton sera pour connecter
      # Force l'onglet "Grbl output" sauf en cas de debug
      if not self.ui.btnDebug.isChecked():
        self.ui.grpConsole.setCurrentIndex(2)


  @pyqtSlot()
  def on_sig_connect(self):
    self.__connectionStatus = self.__grblCom.isOpen()
    if self.__connectionStatus:
      # Mise a jour de l'interface
      self.ui.lblConnectStatus.setText(self.tr("Connecte a {}").format(self.ui.cmbPort.currentText().split("-")[0].strip()))
      self.ui.btnConnect.setText(self.tr("Deconnecter")) # La prochaine action du bouton sera pour deconnecter
      self.setEnableDisableConnectControls()
      # Active les groupes de controles de pilotage de Grbl
      self.setEnableDisableGroupes()
    else:
      # Mise a jour de l'interface
      self.ui.lblConnectStatus.setText(self.tr("<Non Connecte>"))
      self.ui.btnConnect.setText(self.tr("Connecter")) # La prochaine action du bouton sera pour connecter
      self.__statusText = ""
      self.ui.statusBar.showMessage(self.__statusText)
      self.setEnableDisableConnectControls()
      # Force la position de l'arret d'urgence
      self.__arretUrgence = True
      # Active les groupes de controles de pilotage de Grbl
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


  @pyqtSlot(float)
  def on_dsbJogSpeed_valueChanged(self, val: float):
    self.__jog.setJogSpeed(val)


  @pyqtSlot()
  def on_btnSpinM3(self):
    self.__grblCom.gcodeInsert("M3")
    self.ui.btnSpinM4.setEnabled(False) # Interdit un changement de sens de rotation direct


  @pyqtSlot()
  def on_btnSpinM4(self):
    self.__grblCom.gcodeInsert("M4")
    self.ui.btnSpinM3.setEnabled(False) # Interdit un changement de sens de rotation direct


  @pyqtSlot()
  def on_btnSpinM5(self):
    self.__grblCom.gcodeInsert("M5")
    self.ui.btnSpinM3.setEnabled(True)
    self.ui.btnSpinM4.setEnabled(True)


  @pyqtSlot()
  def on_btnFloodM7(self):
    if self.decode.get_etatArrosage() != "M7" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutot que self.__grblCom.enQueue("M7")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)


  @pyqtSlot()
  def on_btnFloodM8(self):
    if self.decode.get_etatArrosage() != "M8" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutot que self.__grblCom.enQueue("M8")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot()
  def on_btnFloodM9(self):
    if self.decode.get_etatArrosage() == "M7" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)
    if self.decode.get_etatArrosage() == "M8" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command" plutot que self.__grblCom.enQueue("M9")
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot(str, QtGui.QMouseEvent)
  def on_lblG5xClick(self, lblText, e):
    ###print(e)
    self.__grblCom.gcodeInsert(lblText)


  @pyqtSlot()
  def on_btnKillAlarm(self):
    self.__grblCom.gcodeInsert(CMD_GRBL_KILL_ALARM_LOCK)


  @pyqtSlot()
  def on_btnHomeCycle(self):
    self.__grblCom.gcodeInsert(CMD_GRBL_RUN_HOME_CYCLE)


  @pyqtSlot()
  def on_btnReset(self):
    self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET)


  @pyqtSlot()
  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      if self.ui.txtGCode.text() == REAL_TIME_REPORT_QUERY:
        self.decode.getNextStatus()
      if self.ui.txtGCode.text() == CMD_GRBL_GET_GCODE_PARAMATERS:
        self.decode.getNextGCodeParams()
      if self.ui.txtGCode.text() == CMD_GRBL_GET_GCODE_STATE:
        self.decode.getNextGCodeState()
    self.__grblCom.gcodePush(self.ui.txtGCode.text())
    self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
    self.ui.txtGCode.setFocus()
    if self.ui.txtGCode.text() != "":
      self.__gcodes_stack.insert(0, self.ui.txtGCode.text())
      self.__gcodes_stack_pos = 0
      self.__gcode_current_txt = ""


  @pyqtSlot()
  def txtGCode_on_Change(self):
    if self.ui.txtGCode.text() == REAL_TIME_REPORT_QUERY:
      self.logGrbl.append(REAL_TIME_REPORT_QUERY)
      self.decode.getNextStatus()
      self.__grblCom.realTimePush(REAL_TIME_REPORT_QUERY) # Envoi direct ? sans attendre le retour chariot.
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
    if not self.__gcode_recall_flag:
      self.__gcodes_stack_pos = -1
    else:
      self.__gcode_recall_flag = False


  @pyqtSlot(QtGui.QKeyEvent)
  def on_keyPressed(self, e):
    key = e.key()
    if QKeySequence(key+int(e.modifiers())) == QKeySequence("Ctrl+C"):
      pass
    elif QKeySequence(key+int(e.modifiers())) == QKeySequence("Ctrl+X"):
      self.logGrbl.append("Ctrl+X")
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    elif key == Qt.Key_Up:
      # Rappel des dernières commandes GCode
      if len(self.__gcodes_stack) > 0:
        if self.__gcode_current_txt == "":
          self.__gcode_current_txt = self.ui.txtGCode.text()
        self.__gcodes_stack_pos += 1
        if self.__gcodes_stack_pos >= 0 and self.__gcodes_stack_pos < len(self.__gcodes_stack):
          self.__gcode_recall_flag = True
          self.ui.txtGCode.setText(self.__gcodes_stack[self.__gcodes_stack_pos])
          self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
        elif self.__gcodes_stack_pos >= len(self.__gcodes_stack):
          self.__gcodes_stack_pos = len(self.__gcodes_stack) - 1
    elif key == Qt.Key_Down:
      # Rappel des dernières commandes GCode
      if len(self.__gcodes_stack) > 0:
        self.__gcodes_stack_pos -= 1
        if self.__gcodes_stack_pos >= 0 and self.__gcodes_stack_pos < len(self.__gcodes_stack):
          self.__gcode_recall_flag = True
          self.ui.txtGCode.setText(self.__gcodes_stack[self.__gcodes_stack_pos])
          self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
        elif self.__gcodes_stack_pos < 0:
          self.ui.txtGCode.setText(self.__gcode_current_txt)
          self.__gcodes_stack_pos = -1

  @pyqtSlot(int, str)
  def on_sig_log(self, severity: int, data: str):
    if severity == logSeverity.info.value:
      self.logCn5X.setTextColor(TXT_COLOR_GREEN)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Info    : " + data)
    elif severity == logSeverity.warning.value:
      self.logCn5X.setTextColor(TXT_COLOR_ORANGE)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Warning : " + data)
      if not self.ui.btnDebug.isChecked():
        self.ui.grpConsole.setCurrentIndex(2)
    elif severity == logSeverity.error.value:
      self.logCn5X.setTextColor(TXT_COLOR_RED)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Error   : " + data)
      if not self.ui.btnDebug.isChecked():
        self.ui.grpConsole.setCurrentIndex(2)
  def log(self, severity: int, data: str):
    self.on_sig_log(severity, data)

  @pyqtSlot(str)
  def on_sig_init(self, data: str):
    self.log(logSeverity.info.value, self.tr("cn5X++ : Grbl initialise."))
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
    # Repere la chaine "[AXS:5:XYZAB]" pour recuperer le nombre d'axes et leurs noms
    if data[:5] == "[AXS:":
      self.__nbAxis           = int(data[1:-1].split(':')[1])
      self.__axisNames        = list(data[1:-1].split(':')[2])
      if len(self.__axisNames) < self.__nbAxis:
        # Il est posible qu'il y ait moins de lettres que le nombre d'axes si Grbl
        # implémente l'option REPORT_VALUE_FOR_AXIS_NAME_ONCE
        self.__nbAxis = len(self.__axisNames);
      self.updateAxisNumber()
      self.decode.setNbAxis(self.__nbAxis)

    if not self.__grblConfigLoaded:
      self.logGrbl.append(data)


  def updateAxisNumber(self):
      self.ui.lblLblPosX.setText(self.__axisNames[0])
      self.ui.lblLblPosY.setText(self.__axisNames[1])
      self.ui.lblLblPosZ.setText(self.__axisNames[2])

      if self.__nbAxis > 3:
        self.ui.lblLblPosA.setText(self.__axisNames[3])
        self.ui.lblLblPosA.setEnabled(True)
        self.ui.lblLblPosA.setStyleSheet("")
        self.ui.lblPosA.setEnabled(True)
        self.ui.lblPosA.setStyleSheet("")
        self.ui.lblG5xA.setStyleSheet("")
        self.ui.lblG92A.setStyleSheet("")
        self.ui.lblWcoA.setStyleSheet("")
      else:
        self.ui.lblLblPosA.setText("")
        self.ui.lblLblPosA.setEnabled(False)
        self.ui.lblLblPosA.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblPosA.setEnabled(False)
        self.ui.lblPosA.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG5xA.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG92A.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblWcoA.setStyleSheet("color: rgb(224, 224, 230);")

      if self.__nbAxis > 4:
        self.ui.lblLblPosB.setText(self.__axisNames[4])
        self.ui.lblLblPosB.setEnabled(True)
        self.ui.lblLblPosB.setStyleSheet("")
        self.ui.lblPosB.setEnabled(True)
        self.ui.lblPosB.setStyleSheet("")
        self.ui.lblG5xB.setStyleSheet("")
        self.ui.lblG92B.setStyleSheet("")
        self.ui.lblWcoB.setStyleSheet("")
      else:
        self.ui.lblLblPosB.setText("")
        self.ui.lblLblPosB.setEnabled(False)
        self.ui.lblLblPosB.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblPosB.setEnabled(False)
        self.ui.lblPosB.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG5xB.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG92B.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblWcoB.setStyleSheet("color: rgb(224, 224, 230);")

      if self.__nbAxis > 5:
        self.ui.lblLblPosC.setText(self.__axisNames[5])
        self.ui.lblLblPosC.setEnabled(True)
        self.ui.lblLblPosC.setStyleSheet("")
        self.ui.lblPosC.setEnabled(True)
        self.ui.lblPosC.setStyleSheet("")
        self.ui.lblG5xC.setStyleSheet("")
        self.ui.lblG92C.setStyleSheet("")
        self.ui.lblWcoC.setStyleSheet("")
      else:
        self.ui.lblLblPosC.setText("")
        self.ui.lblLblPosC.setEnabled(False)
        self.ui.lblLblPosC.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblPosC.setEnabled(False)
        self.ui.lblPosC.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG5xC.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblG92C.setStyleSheet("color: rgb(224, 224, 230);")
        self.ui.lblWcoC.setStyleSheet("color: rgb(224, 224, 230);")

      if 'A' in self.__axisNames:
        self.ui.btnJogMoinsA.setEnabled(True)
        self.ui.btnJogPlusA.setEnabled(True)
      else:
        self.ui.btnJogMoinsA.setEnabled(False)
        self.ui.btnJogPlusA.setEnabled(False)

      if 'B' in self.__axisNames:
        self.ui.btnJogMoinsB.setEnabled(True)
        self.ui.btnJogPlusB.setEnabled(True)
      else:
        self.ui.btnJogMoinsB.setEnabled(False)
        self.ui.btnJogPlusB.setEnabled(False)

      if 'C' in self.__axisNames:
        self.ui.btnJogMoinsC.setEnabled(True)
        self.ui.btnJogPlusC.setEnabled(True)
      else:
        self.ui.btnJogMoinsC.setEnabled(False)
        self.ui.btnJogPlusC.setEnabled(False)


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
  def on_mnuA_propos(self):
    ''' Appel de la boite de dialogue A Propos
    '''
    dlgApropos = cn5XAPropos(self.tr("Version {}").format(APP_VERSION_STRING), self.__licenceFile)
    dlgApropos.setParent(self)
    dlgApropos.showDialog()


  @pyqtSlot()
  def on_btnDebug(self):
    ''' Set the debug menu on the same status '''
    if self.ui.btnDebug.isChecked():
      if not self.ui.mnuDebug_mode.isChecked():
        self.ui.mnuDebug_mode.setChecked(True)
      self.ui.btnPausePooling.setEnabled(True)
      self.on_sig_debug("cn5X++ (v{}) : Starting debug.".format(APP_VERSION_STRING))
    else:
      self.on_sig_debug("cn5X++ (v{}) : Stop debugging.".format(APP_VERSION_STRING))
      if self.ui.mnuDebug_mode.isChecked():
        self.ui.mnuDebug_mode.setChecked(False)
      # Ensure pooling in active when debug is off
      self.ui.btnPausePooling.setEnabled(False)
      self.ui.btnPausePooling.setChecked(False)
      self.__grblCom.startPooling()


  @pyqtSlot()
  def on_btnPausePooling(self):
    self.log(logSeverity.info.value, "on_btnPausePooling({})".format(self.ui.btnPausePooling.isChecked()))
    if self.ui.btnPausePooling.isChecked():
      self.__grblCom.stopPooling()
    else:
      self.__grblCom.startPooling()


  @pyqtSlot()
  def clearDebug(self):
    self.logDebug.clear()


  def startCycle(self):
    self.log(logSeverity.info.value, self.tr("Demarrage du cycle..."))
    self.__gcodeFile.selectGCodeFileLine(0)
    self.__cycleRun = True
    self.__cyclePause = False
    self.__gcodeFile.enQueue(self.__grblCom)
    self.ui.btnStart.setButtonStatus(True)
    self.ui.btnPause.setButtonStatus(False)
    self.ui.btnStop.setButtonStatus(False)


  def pauseCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      self.log(logSeverity.warning.value, self.tr("Hold en cours, impossible de repartir maintenant."))
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      self.log(logSeverity.info.value, self.tr("Reprise du cycle..."))
      self.__grblCom.realTimePush(REAL_TIME_CYCLE_START_RESUME)
      self.__cyclePause = False
      self.ui.btnStart.setButtonStatus(True)
      self.ui.btnPause.setButtonStatus(False)
      self.ui.btnStop.setButtonStatus(False)
    else:
      self.log(logSeverity.info.value, self.tr("Pause du cycle..."))
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      self.__cyclePause = True
      self.ui.btnStart.setButtonStatus(False)
      self.ui.btnPause.setButtonStatus(True)
      self.ui.btnStop.setButtonStatus(False)


  def stopCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      # Deja en pause, on vide la file d'attente et on envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Arret du cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    elif self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      # Attente que le Hold soit termine
      self.log(logSeverity.info.value, self.tr("Pause en cours avant arret du cycle..."))
      while self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Arret du cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    else:
      # Envoie une pause
      self.log(logSeverity.info.value, self.tr("Pause avant arret du cycle..."))
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      # Attente que le Hold soit termine
      while self.ui.lblEtat.text() != GRBL_STATUS_HOLD0:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Arret du cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    self.__cycleRun = False
    self.__cyclePause = False
    self.ui.btnStart.setButtonStatus(False)
    self.ui.btnPause.setButtonStatus(False)
    self.ui.btnStop.setButtonStatus(True)
    self.log(logSeverity.info.value, self.tr("Cycle termine."))


  def on_gcodeTableContextMenu(self, event):
    if self.__gcodeFile.isFileLoaded():
      self.cMenu = QtWidgets.QMenu(self)
      editAction = QtWidgets.QAction(self.tr("Editer la ligne"), self)
      editAction.triggered.connect(lambda: self.editGCodeSlot(event))
      self.cMenu.addAction(editAction)
      insertAction = QtWidgets.QAction(self.tr("Inserer une ligne"), self)
      insertAction.triggered.connect(lambda: self.insertGCodeSlot(event))
      self.cMenu.addAction(insertAction)
      ajoutAction = QtWidgets.QAction(self.tr("Ajouter une ligne"), self)
      ajoutAction.triggered.connect(lambda: self.ajoutGCodeSlot(event))
      self.cMenu.addAction(ajoutAction)
      supprimeAction = QtWidgets.QAction(self.tr("Supprimer la ligne"), self)
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
    resetAction = QtWidgets.QAction(self.tr("Reinitialiser l'avance a 100%"), self)
    resetAction.triggered.connect(lambda: self.ui.dialAvance.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_dialBrocheContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    resetAction = QtWidgets.QAction(self.tr("Reinitialiser la vitesse de broche a 100%"), self)
    resetAction.triggered.connect(lambda: self.ui.dialBroche.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblPosContextMenu(self, axis: str):
    self.cMenu = QtWidgets.QMenu(self)
    resetX = QtWidgets.QAction(self.tr("Reinitialiser l'axe {} a zero").format(self.__axisNames[axis]), self)
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush("G10 P0 L20 {}0".format(self.__axisNames[axis])))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction(self.tr("Reinitialiser tous les axes a zero"), self)
    gcodeString = "G10 P0 L20 "
    for N in self.__axisNames:
      gcodeString += "{}0 ".format(N)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush(gcodeString))
    self.cMenu.addAction(resetAll)
    self.cMenu.addSeparator()
    resetX = QtWidgets.QAction(self.tr("Retour de {} a la position zero").format(self.__axisNames[axis]), self)
    cmdJog1 = CMD_GRBL_JOG + "G90G21F{}{}0".format(self.ui.dsbJogSpeed.value(), self.__axisNames[axis])
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush(cmdJog1))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction(self.tr("Retour de tous les axes en position zero"), self)
    cmdJog = CMD_GRBL_JOG + "G90G21F{}".format(self.ui.dsbJogSpeed.value())
    for N in self.__axisNames:
      cmdJog += "{}0 ".format(N)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush(cmdJog))
    self.cMenu.addAction(resetAll)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblGXXContextMenu(self, piece: int):
    self.cMenu = QtWidgets.QMenu(self)
    setOrigineAll = QtWidgets.QAction(self.tr("Positionner l'origine piece {} (G{})").format(str(piece), str(piece + 53)), self)

  def on_lblPlanContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    planXY = QtWidgets.QAction(self.tr("Plan de travail G17 - XY (Defaut)"), self)
    planXY.triggered.connect(lambda: self.__grblCom.gcodePush("G17"))
    self.cMenu.addAction(planXY)
    planXZ = QtWidgets.QAction(self.tr("Plan de travail G18 - XZ"), self)
    planXZ.triggered.connect(lambda: self.__grblCom.gcodePush("G18"))
    self.cMenu.addAction(planXZ)
    planYZ = QtWidgets.QAction(self.tr("Plan de travail G19 - YZ"), self)
    planYZ.triggered.connect(lambda: self.__grblCom.gcodePush("G19"))
    self.cMenu.addAction(planYZ)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblUnitesContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction(self.tr("G20 - Unites travail en pouces"), self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G20"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction(self.tr("G21 - Unites travail en millimetres"), self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G21"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblCoordContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction(self.tr("G90 - Deplacements en coordonnees absolues"), self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G90"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction(self.tr("G91 - Deplacements en coordonnees relatives"), self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G91"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


  def createLangMenu(self):
    ''' Creation du menu de choix de la langue du programme
    en fonction du contenu du fichier i18n/cn5X_locales.xml '''
    document = parse("i18n/cn5X_locales.xml")
    root = document.documentElement
    translations = root.getElementsByTagName("translation")

    l = 0
    self.locales = []
    self.ui.actionLang = []
    self.ui.iconLang = []
    for translation in translations:

      self.locales.append(translation.getElementsByTagName("locale")[0].childNodes[0].nodeValue)
      label = translation.getElementsByTagName("label")[0].childNodes[0].nodeValue
      qm_file = translation.getElementsByTagName("qm_file")[0].childNodes[0].nodeValue
      flag_file = translation.getElementsByTagName("flag_file")[0].childNodes[0].nodeValue

      self.ui.actionLang.append(QtWidgets.QAction(self))
      self.ui.iconLang.append(QtGui.QIcon())
      self.ui.iconLang[l].addPixmap(QtGui.QPixmap(flag_file), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      self.ui.actionLang[l].setIcon(self.ui.iconLang[l])
      self.ui.actionLang[l].setText(label)
      self.ui.actionLang[l].setCheckable(True)
      self.ui.actionLang[l].setObjectName(self.locales[l])
      self.ui.menuLangue.addAction(self.ui.actionLang[l])

      l += 1

    self.ui.menuLangue.addSeparator()
    self.actionLangSystem = QtWidgets.QAction()
    self.actionLangSystem.setCheckable(True)
    self.actionLangSystem.setObjectName("actionLangSystem")
    self.ui.menuLangue.addAction(self.actionLangSystem)
    self.actionLangSystem.setText(self.tr("Utiliser la langue du systeme"))

    self.ui.menuLangue.triggered.connect(self.on_menuLangue)


  def on_menuLangue(self, action):
    if action.objectName() == "actionLangSystem":
      locale = QLocale()
      self.settings.remove("lang")
    else:
      locale = QLocale(action.objectName())
      self.settings.setValue("lang", action.objectName())
    # Active la nouvelle langue
    self.setTranslator(locale)
    #for a in self.ui.menuLangue.actions():
    #  if a.objectName() == action.objectName():
    #    a.setChecked(True)
    #  else:
    #    a.setChecked(False)


  def setTranslator(self, locale: QLocale):
    ''' Active la langue de l'interface '''
    global translator # Reutilise le translateur de l'objet app
    if not translator.load(locale, "i18n/cn5X", "."):
      print("Locale ({}) not usable, using default to english".format(locale.name()))
      #locale = QLocale(QLocale.French, QLocale.France)
      locale = QLocale(QLocale.English, QLocale.UnitedKingdom)
      translator.load(locale, "i18n/cn5X", ".")

    # Install le traducteur et l'exécute sur les éléments déjà chargés
    QtCore.QCoreApplication.installTranslator(translator)
    self.ui.retranslateUi(self)
    self.actionLangSystem.setText(self.tr("Utiliser la langue du systeme"))

    # Coche le bon item dans le menu langue
    settingsLang = self.settings.value("lang", "default")
    for a in self.ui.menuLangue.actions():
      if a.objectName() == "actionLangSystem":
        if settingsLang == "default":
          a.setChecked(True)
        else:
          a.setChecked(False)
      else:
        la = QLocale(a.objectName())
        if la.language() == locale.language():
          self.ui.menuLangue.setIcon(a.icon())
          if settingsLang != "default":
            a.setChecked(True)
          else:
            a.setChecked(False)
        else:
          a.setChecked(False)

    # Sélectionne l'image du bouton d'urgence
    if locale.language() == QLocale(QLocale.French, QLocale.France).language():
      self.btnUrgencePictureLocale = ":/cn5X/images/btnUrgence.svg"
      self.btnUrgenceOffPictureLocale = ":/cn5X/images/btnUrgenceOff.svg"
    else:
      self.btnUrgencePictureLocale = ":/cn5X/images/btnEmergency.svg"
      self.btnUrgenceOffPictureLocale = ":/cn5X/images/btnEmergencyOff.svg"
    # et relance l'affichage avec la nouvelle image
    self.setEnableDisableGroupes()

"""******************************************************************"""


if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)

  translator = QTranslator()
  locale = QLocale(QLocale.French, QLocale.France)
  translator.load(locale, "i18n/cn5X", ".")
  app.installTranslator(translator)

  window = winMain()
  window.show()
  sys.exit(app.exec_())
