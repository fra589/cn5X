#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2022 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X.py is part of cn5X++                                    '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
' under the terms of the GNU General Public License as published by       '
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
from datetime import datetime
from xml.dom.minidom import parse, parseString, Node, Element
import locale
import argparse
import serial, serial.tools.list_ports
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QCoreApplication, QObject, QThread, pyqtSignal, pyqtSlot, QModelIndex,  QItemSelectionModel, QFileInfo, QTranslator, QLocale, QSettings, QFile, QEvent
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem, QValidator, QPalette, QFontDatabase
from PyQt5.QtWidgets import QDialog, QAbstractItemView, QMessageBox
from cn5X_config import *
from msgbox import *
from speedOverrides import *
from grblCom import grblCom
from grblDecode import grblDecode
from gcodeQLineEdit import gcodeQLineEdit
from cnQPushButton import cnQPushButton
from grblJog import grblJog
from grblProbe import *
from cn5X_gcodeFile import gcodeFile
from qwprogressbox import *
from qwkeyboard import *
from qwblackscreen import *
from grblConfig import grblConfig
from cn5X_apropos import cn5XAPropos
from cn5X_helpProbe import cn5XHelpProbe
from grblG92 import dlgG92
from grblG28_30_1 import dlgG28_30_1
from cn5X_jog import dlgJog
from cn5X_beep import cn5XBeeper
from cn5X_toolChange import dlgToolChange

import mainWindow


class upperCaseValidator(QValidator):
  def validate(self, string, pos):
    return QValidator.Acceptable, string.upper(), pos


class appEventFilter(QObject):
  def __init__(self, win, parent=None):
    super().__init__()
    self.__win = win

  def eventFilter(self, obj: QObject, event: QEvent) -> bool:
    # mémorise le moment du dernier évennement clavier ou souris
    if event.type() in [QEvent.KeyPress, QEvent.KeyRelease, QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease]:
      maintenant = time.time()
      self.__win.lastActivity = maintenant
      # Masque l'écran de veille si affiché
      if self.__win.blackScreen.isVisible():
        self.__win.blackScreen.blackScreen_hide()
        return True # Bloque la suite du traitement de l'évennement
    return super().eventFilter(obj, event)


class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):

    # Force le curseur souris sablier
    QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)

    QtWidgets.QMainWindow.__init__(self, parent)

    self.ucase = upperCaseValidator(self)
    self.__gcodes_stack = []
    self.__gcodes_stack_pos = -1
    self.__gcode_recall_flag = False
    self.__gcode_current_txt = ""

    self.__settings = QSettings(QSettings.NativeFormat, QSettings.UserScope, ORG_NAME, APP_NAME)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--connect", action="store_true", help=self.tr("Connect the serial port"))
    parser.add_argument("-f", "--file", help=self.tr("Load the GCode file"))
    parser.add_argument("-l", "--lang", help=self.tr("Define the interface language"))
    parser.add_argument("-p", "--port", help=self.tr("select the serial port"))
    parser.add_argument("-s", "--fullScreen", action="store_true", help=self.tr("Set appliation full screen mode"))
    parser.add_argument("-u", "--noUrgentStop", action="store_true", help=self.tr("Unlock urgent stop"))
    self.__args = parser.parse_args()

    # Retrouve le fichier de licence dans le même répertoire que l'exécutable
    self.__licenceFile = "{}/COPYING".format(app_path)

    # Initialise la fenêtre princpale
    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)
    
    # Affichage plein écran et screen saver
    fullScreenSetting = self.__settings.value("displayFullScreen", False, type=bool)

    if self.__args.fullScreen != False:
      # L'argument de la ligne de commande est prioritaire
      # sur l'état sauvegardé dans les settings
      self.showFullScreen()
      self.ui.mnuDisplay_full_sceen.setChecked(True)
      self.ui.mnuDisplay_black_screen.setEnabled(True)
    else:
      # Pas d'argument enligne de commande,
      # on regarde l'état sauvegardé dans les settings
      if fullScreenSetting:
        self.showFullScreen()
        self.ui.mnuDisplay_full_sceen.setChecked(True)
        self.ui.mnuDisplay_black_screen.setEnabled(True)
      else:
        self.showNormal()
        self.ui.mnuDisplay_full_sceen.setChecked(False)
        self.ui.mnuDisplay_black_screen.setEnabled(False)

    # Widget pour mise en veille
    self.screenSaverClock = self.__settings.value("screenSaverClock", True, type=bool)
    if self.screenSaverClock:
      self.ui.mnuScreenSaverClock.setChecked(True)
    else:
      self.ui.mnuScreenSaverClock.setChecked(False)

    self.blackScreen = qwBlackScreen(self)
    self.timerVeille = QtCore.QTimer()
    self.timerVeille.setInterval(1000) # 1 seconde
    self.timerVeille.timeout.connect(self.veilleEcran)

    # Parametre de mise en veille
    # Valeurs possibles : 1, 5, 20, 60, 120, 360, -1 (off)
    self.__screenSaverTimeout = int(self.__settings.value("screenSaverTimeout", -1))
    self.updateMnuBlackScreen() # Coche le bon élément du menu de veille

    # Démarre le timer si veille d'écran active et affiché en plein écran
    if self.__screenSaverTimeout in [1, 5, 20, 60, 120, 360] \
    and self.ui.mnuDisplay_full_sceen.isChecked():
      self.timerVeille.start()

    # Initialise la boite de progression d'un fichier programme GCode
    self.__pBox = qwProgressBox(self)
    
    # initialise le clavier
    self.__qwKeyboard = qwKeyboard(self)
    self.__qwKeyboard.setLinkedTxt(self.ui.txtGCode)
    
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
    self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)               # Active le tab de la log cn5X++

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
    self.__grblCom.sig_activity.connect(self.on_sig_activity)
    self.__grblCom.sig_serialLock.connect(self.on_sig_serialLock)

    self.__beeper = cn5XBeeper();

    self.__arretUrgence     = True
    def arretUrgence():
      return self.__arretUrgence

    self.__decode = grblDecode(self.ui, self.log, self.__grblCom, self.__beeper, arretUrgence)
    self.__pBox.setDecoder(self.__decode)    
    self.__grblCom.setDecodeur(self.__decode)

    # Boite de dialogue de changement d'outils
    self.__dlgToolChange = dlgToolChange(self, self.__grblCom, self.__decode, DEFAULT_NB_AXIS, DEFAULT_AXIS_NAMES)
    self.__dlgToolChange.setParent(self)

    self.__gcodeFile = gcodeFile(self.ui, self.ui.gcodeTable, self.__dlgToolChange)
    self.__gcodeFile.sig_log.connect(self.on_sig_log)

    self.__jog = grblJog(self.__grblCom)
    self.ui.dsbJogSpeed.setValue(DEFAULT_JOG_SPEED)
    self.ui.dsbJogSpeed.valueChanged.connect(self.on_dsbJogSpeed_valueChanged)

    self.__probe = grblProbe(self.__grblCom)
    self.__probe.sig_log.connect(self.on_sig_log)
    self.__probeResult       = None
    
    self.__connectionStatus = False
    self.__cycleRun         = False
    self.__cyclePause       = False
    self.__grblConfigLoaded = False
    self.__nbAxis           = DEFAULT_NB_AXIS
    self.__axisNames        = DEFAULT_AXIS_NAMES
    self.__decode.updateAxisDefinition()
    self.__maxTravel        = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    self.__firstGetSettings = False
    self.__jogModContinue   = False

    '''---------- Preparation de l'interface ----------'''

    # On traite la langue locale.
    if self.__args.lang != None:
      # l'argument sur la ligne de commande est prioritaire.
      langue = QLocale(self.__args.lang)
    else:
      # Si une langue est définie dans les settings, on l'applique
      settingsLang = self.__settings.value("lang", "default")
      if settingsLang != "default":
        langue = QLocale(settingsLang)
      else:
        # On prend la locale du système par défaut
        langue = QLocale()

    self.setTranslator(langue)

    QtGui.QFontDatabase.addApplicationFont(":/cn5X/fonts/LEDCalculator.ttf")  # Police type "LED"
    self.ui.btnConnect.setText(self.tr("Connect"))                            # Label du bouton connect
    self.populatePortList()                                                   # On rempli la liste des ports serie

    app.setStyleSheet("QToolTip { background-color: rgb(248, 255, 192); color: rgb(0, 0, 63); }")

    curIndex = -1                                                             # On rempli la liste des vitesses
    for v in serial.Serial.BAUDRATES:
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == COM_DEFAULT_BAUD_RATE:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenetre (status bar)
    self.__statusText = ""
    self.ui.statusBar.showMessage(self.__statusText)

    # flag pour mise à jour de l'interface résultats probe XY et valeurs de calcul de centre
    self.__xMin      = False
    self.__xMinValue = None
    self.__xMax      = False
    self.__xMaxValue = None
    self.__yMin      = False
    self.__yMinValue = None
    self.__yMax      = False
    self.__yMaxValue = None

    # Flag pour unicité de la boite de dialogue Jog
    self.dlgJog = None

    self.iconLinkOn  = QtGui.QIcon()
    self.iconLinkOff = QtGui.QIcon()
    self.iconLinkOn.addPixmap(QtGui.QPixmap(":/cn5X/images/btnLinkOn.svg"), QtGui.QIcon.Normal, QtGui.QIcon.On)
    self.iconLinkOff.addPixmap(QtGui.QPixmap(":/cn5X/images/btnLinkOff.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

    '''---------- Connections des evennements de l'interface graphique ----------'''
    
    self.ui.btnUrgence.pressed.connect(self.on_arretUrgence)             # Evenements du bouton d'arret d'urgence
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed) # un clic sur un element de la liste appellera la methode 'on_cmbPort_changed'

    self.ui.mnuBar.hovered.connect(self.on_mnuBar)     # Connexions des routines du menu application
    self.ui.mnuAppOuvrir.triggered.connect(self.on_mnuAppOuvrir)
    self.ui.mnuAppEnregistrer.triggered.connect(self.on_mnuAppEnregistrer)
    self.ui.mnuAppEnregistrerSous.triggered.connect(self.on_mnuAppEnregistrerSous)
    self.ui.mnuAppFermerGCode.triggered.connect(self.on_mnuAppFermerGCode)

    self.ui.mnuPreferences.aboutToShow.connect(self.on_mnuPreferences)
    self.ui.mnuConfirm_Go_to_G28.triggered.connect(self.on_mnuConfirm_Go_to_G28)
    self.ui.mnuConfirm_Go_to_G30.triggered.connect(self.on_mnuConfirm_Go_to_G30)
    self.ui.mnuConfirm_define_G28.triggered.connect(self.on_mnuConfirm_define_G28)
    self.ui.mnuConfirm_define_G30.triggered.connect(self.on_mnuConfirm_define_G30)
    self.ui.mnuPrefToolChange.triggered.connect(self.on_mnuPrefToolChange)
    self.ui.mnuIgnoreFirstToolChange.triggered.connect(self.on_mnuIgnoreFirstToolChange)

    self.ui.mnuAppQuitter.triggered.connect(self.on_mnuAppQuitter)

    self.ui.mnu_GrblConfig.triggered.connect(self.on_mnu_GrblConfig)
    self.ui.mnu_MPos.triggered.connect(self.on_mnu_MPos)
    self.ui.mnu_WPos.triggered.connect(self.on_mnu_WPos)
    # Sous menu Machine/Set orifine
    self.ui.mnuG5X_origine_0.triggered.connect(lambda: self.on_mnuG5X_origine(0))
    self.ui.mnuG5X_origine_1.triggered.connect(lambda: self.on_mnuG5X_origine(1))
    self.ui.mnuG5X_origine_2.triggered.connect(lambda: self.on_mnuG5X_origine(2))
    self.ui.mnuG5X_origine_3.triggered.connect(lambda: self.on_mnuG5X_origine(3))
    self.ui.mnuG5X_origine_4.triggered.connect(lambda: self.on_mnuG5X_origine(4))
    self.ui.mnuG5X_origine_5.triggered.connect(lambda: self.on_mnuG5X_origine(5))
    self.ui.mnuG5X_origine_6.triggered.connect(lambda: self.on_mnuG5X_origine(6))
    self.ui.mnuG5X_reset.triggered.connect(self.on_mnuG5X_reset)
    self.ui.mnuG92.triggered.connect(self.on_mnuG92)
    self.ui.mnuSaveG92.triggered.connect(self.on_mnuSaveG92)
    self.ui.mnuRestoreG92.triggered.connect(self.on_mnuRestoreG92)
    self.ui.mnuG92_1.triggered.connect(self.on_mnuG92_1)

    self.ui.mnuJog_to.triggered.connect(self.on_mnuJog_to)
    self.ui.mnuToolChange.triggered.connect(self.on_mnuToolChange)

    # Sous-menu G28/G30
    self.ui.mnuPredefinedLocations.aboutToShow.connect(self.on_mnuPredefinedLocations)
    self.ui.mnuGoToG28.triggered.connect(self.on_gotoG28)
    self.ui.mnuGoToG30.triggered.connect(self.on_gotoG30)
    self.ui.mnuDefineG28.triggered.connect(self.on_mnuDefineG28)
    self.ui.mnuDefineG30.triggered.connect(self.on_mnuDefineG30)

    self.ui.mnuDebug_mode.triggered.connect(self.on_mnuDebug_mode)
    self.ui.mnuResetSerial.triggered.connect(self.on_mnuResetSerial)

    # Menu Display
    self.ui.mnuDisplay_full_sceen.triggered.connect(self.on_mnuDisplay_full_sceen)
    self.ui.mnuBlackScreen0.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(0))
    self.ui.mnuBlackScreen1.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(1))
    self.ui.mnuBlackScreen5.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(5))
    self.ui.mnuBlackScreen20.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(20))
    self.ui.mnuBlackScreen60.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(60))
    self.ui.mnuBlackScreen120.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(120))
    self.ui.mnuBlackScreen360.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(360))
    self.ui.mnuBlackScreenOff.triggered.connect(lambda: self.on_mnuDisplayBlackScreen(-1))
    self.ui.mnuScreenSaverClock.triggered.connect(self.on_mnuScreenSaverClock)

    # Menu d'aide
    self.ui.mnuHelpProbe_single_axis.triggered.connect(lambda: self.on_mnuHelpProbe(MENU_SINGLE_AXIS))
    self.ui.mnuHelpProbe_inside_corner.triggered.connect(lambda: self.on_mnuHelpProbe(MENU_INSIDE_CORNER))
    self.ui.mnuHelpProbe_outside_corner.triggered.connect(lambda: self.on_mnuHelpProbe(MENU_OUTSIDE_CORNER))
    self.ui.mnuHelpProbe_inside_center.triggered.connect(lambda: self.on_mnuHelpProbe(MENU_INSIDE_CENTER))
    self.ui.mnuHelpProbe_outside_center.triggered.connect(lambda: self.on_mnuHelpProbe(MENU_OUTSIDE_CENTER))
    self.ui.mnuA_propos.triggered.connect(self.on_mnuA_propos)

    self.ui.btnRefresh.clicked.connect(self.populatePortList)            # Refresh de la liste des ports serie
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)           # un clic sur le bouton "(De)Connecter" appellera la methode 'action_btnConnect'
    self.ui.btnKeyboard.pressed.connect(self.showKeyboard)               # Bouton d'affichage du clavier touch screen
    self.ui.btnSend.pressed.connect(self.sendCmd)                        # Bouton d'envoi de commandes unitaires
    self.ui.txtGCode.setValidator(self.ucase)                            # Force la saisie des GCodes en majuscules
    self.ui.txtGCode.returnPressed.connect(self.sendCmd)                 # Meme fonction par la touche entree que le bouton d'envoi
    self.ui.txtGCode.textChanged.connect(self.txtGCode_on_Change)        # Analyse du champ de saisie au fur et a mesure de son edition
    self.ui.txtGCode.keyPressed.connect(self.on_keyPressed)
    self.ui.btnDebug.clicked.connect(self.on_btnDebug)
    self.ui.btnPausePooling.clicked.connect(self.on_btnPausePooling)

    self.ui.btnClearDebug.clicked.connect(self.clearDebug)

    self.ui.btnM64P0.clicked.connect(lambda: self.on_btnM64(0))
    self.ui.btnM64P1.clicked.connect(lambda: self.on_btnM64(1))
    self.ui.btnM64P2.clicked.connect(lambda: self.on_btnM64(2))
    self.ui.btnM64P3.clicked.connect(lambda: self.on_btnM64(3))

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

    # Jogging buttons
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

    self.ui.btnJogMoinsX.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusX.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogMoinsY.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusY.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogMoinsZ.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusZ.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogMoinsA.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusA.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogMoinsB.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusB.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogMoinsC.mouseRelease.connect(self.stop_jog)
    self.ui.btnJogPlusC.mouseRelease.connect(self.stop_jog)
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
    self.ui.btnG28.clicked.connect(self.on_gotoG28)
    self.ui.btnG30.clicked.connect(self.on_gotoG30)
    self.ui.gcodeTable.customContextMenuRequested.connect(self.on_gcodeTableContextMenu)
    QtWidgets.QShortcut(QtCore.Qt.Key_F7, self.ui.gcodeTable, activated=self.on_GCodeTable_key_F7_Pressed)
    QtWidgets.QShortcut(QtCore.Qt.Key_F8, self.ui.gcodeTable, activated=self.on_GCodeTable_key_F8_Pressed)
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

    self.ui.rbtProbeInsideXY.toggled.connect(self.setProbeButtonsToolTip)
    
    # Changement d'onglets
    self.__currentQTabMainIndex = self.ui.qtabMain.currentIndex()
    self.ui.qtabMain.currentChanged.connect(self.on_qtabMain_currentChanged)

    # Boutons de probe Z
    self.ui.btnProbeZ.clicked.connect(self.on_btnProbeZ)
    self.ui.btnSaveToolChangePosition.clicked.connect(self.on_btnSaveToolChangePosition)
    self.ui.btnGoToSensor.clicked.connect(self.on_btnGoToSensor)
    self.ui.btnG49.clicked.connect(self.on_btnG49)
    self.ui.btnG43_1.clicked.connect(self.on_btnG43_1)
    self.ui.btnSetOriginZ.clicked.connect(self.on_btnSetOriginZ)
    self.ui.chkSeekZ.clicked.connect(self.on_chkSeekZ)
    self.ui.chkSeekXY.clicked.connect(self.on_chkSeekXY)
    self.ui.chkInvertProbePinZ.clicked.connect(self.on_chkInvertProbePinZ)

    # Onglet probe XY
    self.ui.dsbToolDiameter.valueChanged.connect(self.on_dsbToolDiameterValueChanged)
    self.ui.chkAddOffsetX.stateChanged.connect(self.on_chkAddOffsetXstateChanged)
    self.ui.chkAddOffsetY.stateChanged.connect(self.on_chkAddOffsetYstateChanged)
    self.ui.btnProbeXY_0.clicked.connect(lambda: self.on_btnProbeXY(0))
    self.ui.btnProbeXY_1.clicked.connect(lambda: self.on_btnProbeXY(1))
    self.ui.btnProbeXY_2.clicked.connect(lambda: self.on_btnProbeXY(2))
    self.ui.btnProbeXY_3.clicked.connect(lambda: self.on_btnProbeXY(3))
    self.ui.btnProbeXY_4.clicked.connect(lambda: self.on_btnProbeXY(4))
    self.ui.btnProbeXY_5.clicked.connect(lambda: self.on_btnProbeXY(5))
    self.ui.btnProbeXY_6.clicked.connect(lambda: self.on_btnProbeXY(6))
    self.ui.btnProbeXY_7.clicked.connect(lambda: self.on_btnProbeXY(7))
    self.ui.btnProbeXY_8.clicked.connect(lambda: self.on_btnProbeXY(8))
    self.ui.btnHomeMoinsX.clicked.connect(lambda: self.on_btnHomeXY("moinsX"))
    self.ui.btnHomeMoinsY.clicked.connect(lambda: self.on_btnHomeXY("moinsY"))
    self.ui.btnHomeCenterXY.clicked.connect(lambda: self.on_btnHomeXY("centerXY"))
    self.ui.btnHomeCenterX.clicked.connect(lambda: self.on_btnHomeXY("centerX"))
    self.ui.btnHomeCenterY.clicked.connect(lambda: self.on_btnHomeXY("centerY"))
    self.ui.btnHomePlusX.clicked.connect(lambda: self.on_btnHomeXY("plusX"))
    self.ui.btnHomePlusY.clicked.connect(lambda: self.on_btnHomeXY("plusY"))
    self.ui.btnResetResults.clicked.connect(self.resetProbeResults)
    self.ui.chkInvertProbePinXY.clicked.connect(self.on_chkInvertProbePinXY)

    #--------------------------------------------------------------------------------------
    # Traitement des arguments de la ligne de commande
    #--------------------------------------------------------------------------------------
    if self.__args.connect:
      # Connection du port serie
      self.action_btnConnect()

    if self.__args.file != None:
      # Charge le fichier GCode a l'ouverture
      RC = self.__gcodeFile.readFile(self.__args.file)
      if RC:
        # Selectionne l'onglet du fichier sauf en cas de debug actif
        if not self.ui.btnDebug.isChecked():
          self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_FILE)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.fileName())
      else:
        # Selectionne l'onglet de la console pour que le message d'erreur s'affiche sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)

    if self.__args.noUrgentStop:
      self.__arretUrgence = False
      self.log(logSeverity.info.value, self.tr("Urgent stop unlocked."))

    # Initialise l'etat d'activation ou non des controles
    # En fonction de la selection du port serie ou non
    self.setEnableDisableConnectControls()
    # Active ou desactive les boutons de cycle
    self.setEnableDisableGroupes()

    # Restore le curseur souris sablier en fin d'initialisation
    QtWidgets.QApplication.restoreOverrideCursor()
    
    # Memorise le moment de la dernière activité sur l'interface
    # (clavier ou souris)
    self.lastActivity = time.time()
    
    ### GBGB tests ###
    ###print(locale.getlocale(locale.LC_TIME))
    ###print(datetime.now().strftime("%A %x %H:%M:%S"))
    ### Pour debug de qwProgressBox 
    ###self.__pBox.start()


  @property
  def lastActivity(self):
    return self._lastActivity


  @lastActivity.setter
  def lastActivity(self, value):
    self._lastActivity = value


  def populatePortList(self):
    ''' Rempli la liste des ports serie '''
    # Récupère le dernier utilisé dans les settings
    lastPort = self.__settings.value("grblDevice", "")
    self.ui.cmbPort.clear()
    self.ui.cmbPort.addItem("")
    ports = serial.tools.list_ports.comports(True)
    if len(ports) > 0:
      for p in ports:
        self.ui.cmbPort.addItem(p.device + ' - ' + p.description)
        if self.__args.port is not None:
          if self.__args.port == p.device:
            self.ui.cmbPort.setCurrentIndex(len(self.ui.cmbPort)-1)
        elif lastPort == p.device:
          self.ui.cmbPort.setCurrentIndex(len(self.ui.cmbPort)-1)
    else:
      m = msgBox(
                  title  = self.tr("Warning !"),
                  text   = self.tr("No communication port available!"),
                  info   = self.tr("{} could not find a serial port allowing to communicate with grbl.").format(sys.argv[0]),
                  icon   = msgIconList.Information,
                  detail = self.tr("\nclass serialCom:\n\"serial.tools.list_ports.comports()\" did not return any port."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
    # S'il n'y a qu'un seul port serie et que l'on a rien precise comme option port, on le selectionne
    if self.__args.port == None:
      if len(ports) == 1:
        self.ui.cmbPort.setCurrentIndex(1)
    # Definit l'activation des controles en fonction de la selection du port serie ou non
    self.setEnableDisableConnectControls()


  def setProbeButtonsToolTip(self):
    '''Change probe XY interface intérieur ou extérieur'''
    if self.ui.rbtProbeInsideXY.isChecked():
      self.ui.btnProbeXY_0.changeIcon(":/cn5X/images/btnProbeInCercle.svg")
      self.ui.btnProbeXY_0.setToolTip(self.tr('Run probe in X+, X-, Y+ and Y- direction to find inside center.'))
      self.ui.btnProbeXY_1.changeIcon(":/cn5X/images/btnProbeInX-Y+.svg")
      self.ui.btnProbeXY_1.setToolTip(self.tr('Run probe in X- and Y+ direction.'))
      self.ui.btnProbeXY_2.changeIcon(":/cn5X/images/btnProbeInY+.svg")
      self.ui.btnProbeXY_2.setToolTip("Run probe in Y+ direction.")
      self.ui.btnProbeXY_3.changeIcon(":/cn5X/images/btnProbeInX+Y+.svg")
      self.ui.btnProbeXY_3.setToolTip(self.tr('Run probe in X+ and Y+ direction.'))
      self.ui.btnProbeXY_4.changeIcon(":/cn5X/images/btnProbeInX+.svg")
      self.ui.btnProbeXY_4.setToolTip("Run probe in X+ direction.")
      self.ui.btnProbeXY_5.changeIcon(":/cn5X/images/btnProbeInX+Y-.svg")
      self.ui.btnProbeXY_5.setToolTip(self.tr('Run probe in X+ and Y- direction.'))
      self.ui.btnProbeXY_6.changeIcon(":/cn5X/images/btnProbeInY-.svg")
      self.ui.btnProbeXY_6.setToolTip("Run probe in Y- direction.")
      self.ui.btnProbeXY_7.changeIcon(":/cn5X/images/btnProbeInX-Y-.svg")
      self.ui.btnProbeXY_7.setToolTip(self.tr('Run probe in X- and Y- direction.'))
      self.ui.btnProbeXY_8.changeIcon(":/cn5X/images/btnProbeInX-.svg")
      self.ui.btnProbeXY_8.setToolTip("Run probe in X- direction.")
    
    else: # self.ui.rbtProbeOutsideXY.isChecked()
      self.ui.btnProbeXY_0.changeIcon(":/cn5X/images/btnProbeOutCercle.svg")
      self.ui.btnProbeXY_0.setToolTip(self.tr('Run probe in X+, X-, Y+ and Y- direction to find outside center.'))
      self.ui.btnProbeXY_1.changeIcon(":/cn5X/images/btnProbeOutX+Y-.svg")
      self.ui.btnProbeXY_1.setToolTip(self.tr('Run probe in X+ and Y- direction.'))
      self.ui.btnProbeXY_2.changeIcon(":/cn5X/images/btnProbeOutY-.svg")
      self.ui.btnProbeXY_2.setToolTip("Run probe in Y- direction.")
      self.ui.btnProbeXY_3.changeIcon(":/cn5X/images/btnProbeOutX-Y-.svg")
      self.ui.btnProbeXY_3.setToolTip(self.tr('Run probe in X- and Y- direction.'))
      self.ui.btnProbeXY_4.changeIcon(":/cn5X/images/btnProbeOutX-.svg")
      self.ui.btnProbeXY_4.setToolTip("Run probe in X- direction.")
      self.ui.btnProbeXY_5.changeIcon(":/cn5X/images/btnProbeOutX-Y+.svg")
      self.ui.btnProbeXY_5.setToolTip(self.tr('Run probe in X- and Y+ direction.'))
      self.ui.btnProbeXY_6.changeIcon(":/cn5X/images/btnProbeOutY+.svg")
      self.ui.btnProbeXY_6.setToolTip("Run probe in Y+ direction.")
      self.ui.btnProbeXY_7.changeIcon(":/cn5X/images/btnProbeOutX+Y+.svg")
      self.ui.btnProbeXY_7.setToolTip(self.tr('Run probe in X+ and Y+ direction.'))
      self.ui.btnProbeXY_8.changeIcon(":/cn5X/images/btnProbeOutX+.svg")
      self.ui.btnProbeXY_8.setToolTip("Run probe in X+ direction.")
    

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
      self.ui.btnUrgence.setToolTip(self.tr("Double click to\nunlock the emergency stop"))
      self.ui.frmArretUrgence.setEnabled(False)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.tabMainPage.setEnabled(False)
      self.ui.tabProbeXY.setEnabled(False)
      self.ui.tabProbeZ.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    elif self.__arretUrgence:
      # Connecte mais sous arret d'urgence : Tout est desactive sauf l'arret d'urgence
      self.ui.btnUrgence.setIcon(QtGui.QIcon(self.btnUrgenceOffPictureLocale))
      self.ui.btnUrgence.setToolTip(self.tr("Double click to\nunlock the emergency stop"))
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.tabMainPage.setEnabled(False)
      self.ui.tabProbeXY.setEnabled(False)
      self.ui.tabProbeZ.setEnabled(False)
      self.ui.frmHomeAlarm.setEnabled(False)
    else:
      # Tout est en ordre, on active tout
      self.ui.btnUrgence.setIcon(QtGui.QIcon(self.btnUrgencePictureLocale))
      self.ui.btnUrgence.setToolTip(self.tr("Emergency stop"))
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(True)
      self.ui.grpJog.setEnabled(True)
      self.ui.frmGcodeInput.setEnabled(True)
      self.ui.tabMainPage.setEnabled(True)
      self.ui.tabProbeXY.setEnabled(True)
      self.ui.tabProbeZ.setEnabled(True)
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
      self.ui.mnuResetSerial.setEnabled(True)
      if self.__arretUrgence:
        self.ui.mnu_GrblConfig.setEnabled(True)
        self.ui.mnuSet_origine.setEnabled(False)
        self.ui.mnuPredefinedLocations.setEnabled(False)
        self.ui.mnuJog_to.setEnabled(False)
        self.ui.mnuToolChange.setEnabled(False)
      else:
        self.ui.mnu_GrblConfig.setEnabled(False)
        self.ui.mnuSet_origine.setEnabled(True)
        self.ui.mnuPredefinedLocations.setEnabled(True)
        self.ui.mnuJog_to.setEnabled(True)
        self.ui.mnuToolChange.setEnabled(True)
    else:
      self.ui.mnu_MPos.setEnabled(False)
      self.ui.mnu_WPos.setEnabled(False)
      self.ui.mnuSet_origine.setEnabled(False)
      self.ui.mnuPredefinedLocations.setEnabled(False)
      self.ui.mnuJog_to.setEnabled(False)
      self.ui.mnuToolChange.setEnabled(False)
      self.ui.mnuResetSerial.setEnabled(False)
      self.ui.mnu_GrblConfig.setEnabled(False)


  @pyqtSlot()
  def on_mnuAppOuvrir(self):
    # Affiche la boite de dialogue d'ouverture
    fileName = self.__gcodeFile.showFileOpen()
    if fileName[0] != "":
      # Lecture du fichier
      # Curseur sablier
      QtWidgets.QApplication.setOverrideCursor(Qt.WaitCursor)
      RC = self.__gcodeFile.readFile(fileName[0])
      if RC:
        # Selectionne l'onglet du fichier sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_FILE)
        self.setWindowTitle(APP_NAME + " - " + self.__gcodeFile.fileName())
      else:
        # Selectionne l'onglet de la console pour que le message d'erreur s'affiche sauf en cas de debug
        if not self.ui.btnDebug.isChecked():
          self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)
    # Active ou desactive les boutons de cycle
    self.setEnableDisableGroupes()
    # Restore le curseur de souris
    QtWidgets.QApplication.restoreOverrideCursor()


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
    # Active ou desactive les boutons de cycle
    self.setEnableDisableGroupes()


  @pyqtSlot()
  def on_mnuPreferences(self):
    self.ui.mnuConfirm_Go_to_G28.setChecked(not self.__settings.value("dontConfirmG28", False, type=bool))
    self.ui.mnuConfirm_Go_to_G30.setChecked(not self.__settings.value("dontConfirmG30", False, type=bool))
    self.ui.mnuConfirm_define_G28.setChecked(not self.__settings.value("dontConfirmG28.1", False, type=bool))
    self.ui.mnuConfirm_define_G30.setChecked(not self.__settings.value("dontConfirmG30.1", False, type=bool))
    self.ui.mnuPrefToolChange.setChecked(self.__settings.value("useToolChange", True, type=bool))
    self.ui.mnuIgnoreFirstToolChange.setChecked(self.__settings.value("ignoreFirstToolChange", False, type=bool))


  @pyqtSlot()
  def on_mnuConfirm_Go_to_G28(self):
    self.__settings.setValue("dontConfirmG28", not self.ui.mnuConfirm_Go_to_G28.isChecked())


  @pyqtSlot()
  def on_mnuConfirm_Go_to_G30(self):
    self.__settings.setValue("dontConfirmG30", not self.ui.mnuConfirm_Go_to_G30.isChecked())


  @pyqtSlot()
  def on_mnuConfirm_define_G28(self):
    self.__settings.setValue("dontConfirmG28.1", not self.ui.mnuConfirm_define_G28.isChecked())


  @pyqtSlot()
  def on_mnuConfirm_define_G30(self):
    self.__settings.setValue("dontConfirmG30.1", not self.ui.mnuConfirm_define_G30.isChecked())


  @pyqtSlot()
  def on_mnuPrefToolChange(self):
    self.__settings.setValue("useToolChange", self.ui.mnuPrefToolChange.isChecked())


  @pyqtSlot()
  def on_mnuIgnoreFirstToolChange(self):
    self.__settings.setValue("ignoreFirstToolChange", self.ui.mnuIgnoreFirstToolChange.isChecked())


  @pyqtSlot()
  def on_mnuAppQuitter(self):
    self.close()


  def closeEvent(self, event):
    self.log(logSeverity.info.value, self.tr("Closing the application..."))
    if self.__pBox.isVisible():
      self.__pBox.stop()
    if self.__connectionStatus:
      self.__grblCom.stopCom()
    if not self.__gcodeFile.closeFile():
      self.log(logSeverity.info.value, self.tr("Closing file canceled"))
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
  def on_mnuDisplay_full_sceen(self):
    if self.ui.mnuDisplay_full_sceen.isChecked():
      self.showFullScreen()
      self.ui.mnuDisplay_black_screen.setEnabled(True)
      # Démarre le timer si veille d'écran active et affiché en plein écran
      if self.__screenSaverTimeout in [1, 5, 20, 60, 120, 360]:
        self.timerVeille.start()
      # Mémorise l'état dans les settings
      self.__settings.setValue("displayFullScreen", True)
    else:
      self.showNormal()
      self.ui.mnuDisplay_black_screen.setEnabled(False)
      # Stop le timer de veille d'écran
      self.timerVeille.stop()
      # Mémorise l'état dans les settings
      self.__settings.setValue("displayFullScreen", False)


  @pyqtSlot()
  def on_mnuScreenSaverClock(self):
    if self.ui.mnuScreenSaverClock.isChecked():
      self.screenSaverClock = True
      self.__settings.setValue("screenSaverClock", True)
    else:
      self.screenSaverClock = False
      self.__settings.setValue("screenSaverClock", False)


  @pyqtSlot()
  def on_mnuDisplayBlackScreen(self, duree):
    ''' Parametrage veille écran '''
    if duree == 0:
      # Black screen immédiat et on sort (pas de changement des paramètres
      # sur une mise en veille immédiate)
      self.blackScreen.blackScreen_show()
      return
    elif duree != -1:
      # Démarre le timer
      self.timerVeille.start()
    else:
      # arrete le timer
      self.timerVeille.stop()
    # Mémorise la nouvelle durée
    self.__screenSaverTimeout = duree
    self.__settings.setValue("screenSaverTimeout", duree)
    # met à jour les coches du menu
    self.updateMnuBlackScreen()


  @pyqtSlot()
  def veilleEcran(self):
    ''' Gestion de la veille écran, appelé par le timeout de self.timerVeille '''
    if self.blackScreen.isVisible():
      # Déjà en veille
      return
    dureeLimite = self.__screenSaverTimeout * 60 # timeout stocké en minutes
    dureeInactif = time.time() - self.lastActivity
    if dureeInactif >= dureeLimite:
      # Black screen start
      self.blackScreen.blackScreen_show()


  def updateMnuBlackScreen(self):
    ''' Coche le bon élément du menu de veille '''
    self.ui.mnuBlackScreen1.setChecked(False)
    self.ui.mnuBlackScreen5.setChecked(False)
    self.ui.mnuBlackScreen20.setChecked(False)
    self.ui.mnuBlackScreen60.setChecked(False)
    self.ui.mnuBlackScreen120.setChecked(False)
    self.ui.mnuBlackScreen360.setChecked(False)
    self.ui.mnuBlackScreenOff.setChecked(False)
    if self.__screenSaverTimeout == 1:
      self.ui.mnuBlackScreen1.setChecked(True)
    elif self.__screenSaverTimeout == 5:
      self.ui.mnuBlackScreen5.setChecked(True)
    elif self.__screenSaverTimeout == 20:
      self.ui.mnuBlackScreen20.setChecked(True)
    elif self.__screenSaverTimeout == 60:
      self.ui.mnuBlackScreen60.setChecked(True)
    elif self.__screenSaverTimeout == 120:
      self.ui.mnuBlackScreen120.setChecked(True)
    elif self.__screenSaverTimeout == 360:
      self.ui.mnuBlackScreen360.setChecked(True)
    else:
      # self.__screenSaverTimeout == -1 ou autre valeur non prévue:
      self.ui.mnuBlackScreenOff.setChecked(True)


  @pyqtSlot()
  def on_mnu_GrblConfig(self):
    ''' Appel de la boite de dialogue de configuration
    '''
    self.__grblConfigLoaded = True
    dlgConfig = grblConfig(self.__grblCom, self.__nbAxis, self.__axisNames)
    dlgConfig.setParent(self)
    dlgConfig.sig_config_changed.connect(self.on_sig_config_changed)
    dlgConfig.sig_log.connect(self.on_sig_log)
    dlgConfig.showDialog()
    self.__grblConfigLoaded = False
    # Rafraichi la config
    self.__grblCom.gcodeInsert(CMD_GRBL_GET_SETTINGS)
    self.__grblCom.gcodeInsert(CMD_GRBL_GET_GCODE_PARAMATERS)


  @pyqtSlot()
  def on_mnuG5X_origine(self, axisNum: int):
    if axisNum > 0:
      axisNum -= 1
      self.__grblCom.gcodePush("G10P0L20{}0".format(self.__axisNames[axisNum]))
    else:
      axesTraites = []
      gcodeString = "G10P0L20"
      for a in self.__axisNames:
        if a not in axesTraites:
          gcodeString += "{}0".format(a)
          axesTraites.append(a)
      self.__grblCom.gcodePush(gcodeString)


  @pyqtSlot()
  def on_mnuG5X_reset(self):
    ''' Annulation de tous les offsets G5X '''
    axesTraites = []
    gcodeString = "G10P0L20"
    # Position machine actuelle
    for a in self.__axisNames:
      if a not in axesTraites:
        MPos = self.__decode.getMpos(a)
        gcodeString += "{}{}".format(a, MPos)
        axesTraites.append(a)
    self.__grblCom.gcodePush(gcodeString)


  @pyqtSlot()
  def on_mnuG92(self):
    ''' Appel de la boite de dialogue G92 '''
    dlg = dlgG92(self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
    dlg.setParent(self)
    dlg.showDialog()


  @pyqtSlot()
  def on_mnuSaveG92(self):
    ''' Sauvegarde les valeurs d'offset G92 dans les settings '''
    # Sauvegarde de la topologie machine
    self.__settings.setValue("G92/axisNumber", self.__nbAxis)
    self.__settings.setValue("G92/axisList", "".join(self.__axisNames))
    for i in range(6):
      value = self.__decode.getOffsetG92(i)
      if value is not None:
        self.__settings.setValue("G92/axis_{}".format(i), value)
      else:
        self.__settings.setValue("G92/axis_{}".format(i), None)


  @pyqtSlot()
  def on_mnuRestoreG92(self):
    ''' Restaure les valeurs d'offset G92 depuis les settings'''
    # Vérifie que la topologie est la même (axisNames identique à la définition en cours)
    axisNamesNbSav = self.__settings.value("G92/axisNumber", 0, type=int)
    axisNamesSaved = self.__settings.value("G92/axisList", "<Unknown>")
    if (axisNamesNbSav != self.__nbAxis) or (axisNamesSaved != "".join(self.__axisNames)):
      m = msgBox(
                  title  = self.tr("Error !"),
                  text   = self.tr("Saved axis definition is not identical to the current one!"),
                  info   = "[AXS:{}:{}] != [AXS:{}:{}]".format(axisNamesNbSav, axisNamesSaved, self.__nbAxis, "".join(self.__axisNames)),
                  icon   = msgIconList.Critical,
                  detail = self.tr("Can't restore G92 offsets if the current axis definition (axis number and names) is not the same as the saved one."),
                  stdButton = msgButtonList.Close
                )
      m.afficheMsg()
      return
      
    txtMsg = self.tr("Restore previously saved G92 offsets:\n")
    newValue = [0.0 ,0.0 ,0.0 ,0.0 , 0.0, 0.0]
    axesTraites = []
    for i in range(6):
      newValue[i] = self.__settings.value("G92/axis_{}".format(i), None)
      if newValue[i] is not None:
        if self.__axisNames[i] not in axesTraites:
          txtMsg += "{} = {}, ".format(self.__axisNames[i], newValue[i])
          axesTraites.append(self.__axisNames[i])
        newValue[i] = float(newValue[i])
    txtMsg = txtMsg[:-2] + " ?"
    # Message de confirmation
    m = msgBox(
        title     = self.tr("Restore G92 offsets"),
        text      = txtMsg,
        info      = self.tr("Actuals G92 offsets will be lost."),
        icon      = msgIconList.Question,
        stdButton = msgButtonList.Yes | msgButtonList.Cancel,
        defButton = msgButtonList.Cancel,
        escButton = msgButtonList.Cancel
    )
    if m.afficheMsg() == msgButtonList.Yes:
      # traitement si confirmé
      axesTraites = []
      restoreGcode = "G92"
      for i in range(6):
        actualValue = self.__decode.getOffsetG92(i)
        if actualValue is not None:
          if self.__axisNames[i] not in axesTraites:
            newAxisWpos = self.__decode.getMpos(i) - newValue[i] - self.__decode.getOffsetG5x(i)
            restoreGcode += "{}{}".format(self.__axisNames[i], newAxisWpos)
            axesTraites.append(self.__axisNames[i])
      self.__grblCom.gcodePush(restoreGcode)


  @pyqtSlot()
  def on_mnuG92_1(self):
    ''' Envoi G92.1 '''
    self.__grblCom.gcodePush("G92.1")


  @pyqtSlot()
  def on_mnuJog_to(self):
    ''' Appel de la boite de dialogue Jog '''
    if self.dlgJog is None:
      self.dlgJog = dlgJog(self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
      self.dlgJog.setParent(self)
      self.dlgJog.sig_close.connect(self.on_dlgJogFinished)
      self.dlgJog.showDialog()


  def on_dlgJogFinished(self):
    ''' Supression de la boite de dialogue après fermeture '''
    self.dlgJog.sig_close.disconnect(self.on_dlgJogFinished)
    self.dlgJog = None


  def on_mnuToolChange(self):
    ''' Appel de la boite de dialogue de changement d'outils '''
    RC = self.__dlgToolChange.showDialog()


  @pyqtSlot()
  def on_mnuPredefinedLocations(self):
    if self.__settings.value("dontConfirmG28", False, type=bool):
      self.ui.mnuGoToG28.setText("Go to G28 location")
    else:
      self.ui.mnuGoToG28.setText("Go to G28 location...")
    if self.__settings.value("dontConfirmG30", False, type=bool):
      self.ui.mnuGoToG30.setText("Go to G30 location")
    else:
      self.ui.mnuGoToG30.setText("Go to G30 location...")


  @pyqtSlot()
  def on_gotoG28(self):
    '''
    Make a rapid move from current location to the position defined by the last G28.1
    If no positions are stored with G28.1 then all axes will go to the machine origin.
    '''
    self.ui.btnG28.setButtonStatus(True)
    ''' Appel de la boite de dialogue G28 '''
    dlg = dlgG28_30_1("G28", self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
    dlg.setParent(self)
    dlg.showDialog()
    # On laisse le temps à Grbl de commencer
    jusqua = time.time() + 0.25
    while time.time() < jusqua:
      QCoreApplication.processEvents()
    if self.__decode.get_etatMachine() == GRBL_STATUS_IDLE:
      # La boite de dialogue à ete annulée ou le trajet est déja fini
      self.ui.btnG28.setButtonStatus(False)


  @pyqtSlot()
  def on_gotoG30(self):
    '''
    Make a rapid move from current location to the position defined by the last G30.1
    If no positions are stored with G30.1 then all axes will go to the machine origin.
    '''
    self.ui.btnG30.setButtonStatus(True)
    ''' Appel de la boite de dialogue G30 '''
    dlg = dlgG28_30_1("G30", self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
    dlg.setParent(self)
    dlg.showDialog()
    # On laisse le temps à Grbl de commencer
    jusqua = time.time() + 0.25
    while time.time() < jusqua:
      QCoreApplication.processEvents()
    if self.__decode.get_etatMachine() == GRBL_STATUS_IDLE:
      # La boite de dialogue à ete annulée ou le trajet est déja fini
      self.ui.btnG30.setButtonStatus(False)


  @pyqtSlot()
  def on_mnuDefineG28(self):
    ''' Appel de la boite de dialogue G28.1 '''
    dlg = dlgG28_30_1("G28.1", self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
    dlg.setParent(self)
    dlg.showDialog()


  @pyqtSlot()
  def on_mnuDefineG30(self):
    ''' Appel de la boite de dialogue G30.1 '''
    dlg = dlgG28_30_1("G30.1", self.__grblCom, self.__decode, self.__nbAxis, self.__axisNames)
    dlg.setParent(self)
    dlg.showDialog()


  @pyqtSlot(int)
  def on_qtabMain_currentChanged(self, tabIndex):
    ''' Restore les paramètres de probe à l'activation du Tab concerné '''
    if self.__currentQTabMainIndex != tabIndex:
      if tabIndex == CN5X_TAB_MAIN:
        pass
      elif tabIndex == CN5X_TAB_PROBE_XY:
        # Ajuste les bulles d'aides
        self.setProbeButtonsToolTip()
        # Recharge les dernières valeurs depuis les settings
        self.ui.dsbToolDiameter.setValue(self.__settings.value("Probe/ToolDiameter", DEFAULT_TOOL_DIAMATER, type=float))
        self.ui.dsbDistanceXY.setValue(self.__settings.value("Probe/DistanceXY", DEFAULT_PROBE_DISTANCE, type=float))
        self.ui.dsbClearanceXY.setValue(self.__settings.value("Probe/ClearanceXY", DEFAULT_CLEARANCE_XY, type=float))
        self.ui.dsbClearanceZ.setValue(self.__settings.value("Probe/ClearanceZ", DEFAULT_CLEARANCE_Z, type=float))
        self.ui.dsbFeedRateXY.setValue(self.__settings.value("Probe/FeedRateXY", DEFAULT_PROBE_FEED_RATE, type=float))
        self.ui.chkSeekXY.setChecked(self.__settings.value("Probe/DoubleProbeXY", DEFAULT_PROBE_SEEK, type=bool))
        self.on_chkSeekXY()
        self.ui.dbsSeekRateXY.setValue(self.__settings.value("Probe/SeekRateXY", DEFAULT_PROBE_SEEK_RATE, type=float))
        self.ui.dsbPullOffXY.setValue(self.__settings.value("Probe/PullOffXY", DEFAULT_PROBE_PULL_OFF_DISTANCE_XY, type=float))
        self.ui.gbMoveAfterXY.setChecked(self.__settings.value("Probe/MoveAfterXY", DEFAULT_PROBE_MOVE_AFTER_XY, type=bool))
        self.ui.rbtMove2PointAfterXY.setChecked(self.__settings.value("Probe/go2PointXY", DEFAULT_PROBE_GO_2_POINT_AFTER_XY, type=bool))
        self.ui.rbtRetractAfterXY.setChecked(self.__settings.value("Probe/RetractAfterXY", DEFAULT_PROBE_RETRACT_AFTER_XY, type=bool))
        self.ui.dsbRetractXY.setValue(self.__settings.value("Probe/RetractDistanceXY", DEFAULT_PROBE_RETRACT_DISTANCE_AFTER_XY, type=float))
        # case a cocher invert probe pin
        if self.__decode.getGrblSetting(6) is not None:
          self.ui.chkInvertProbePinXY.setChecked((int(self.__decode.getGrblSetting(6)) == 1))

      elif tabIndex == CN5X_TAB_PROBE_Z:
        self.ui.dsbDistanceZ.setValue(self.__settings.value("Probe/DistanceZ", DEFAULT_PROBE_DISTANCE, type=float))
        self.ui.dsbFeedRateZ.setValue(self.__settings.value("Probe/FeedRateZ", DEFAULT_PROBE_FEED_RATE, type=float))
        self.ui.chkSeekZ.setChecked(self.__settings.value("Probe/DoubleProbeZ", DEFAULT_PROBE_SEEK, type=bool))
        self.on_chkSeekZ()
        self.ui.dbsSeekRateZ.setValue(self.__settings.value("Probe/SeekRateZ", DEFAULT_PROBE_SEEK_RATE, type=float))
        self.ui.dsbPullOffZ.setValue(self.__settings.value("Probe/PullOffZ", DEFAULT_PROBE_PULL_OFF_DISTANCE_Z, type=float))
        self.ui.gbMoveAfterZ.setChecked(self.__settings.value("Probe/MoveAfterZ", DEFAULT_PROBE_MOVE_AFTER_Z, type=bool))
        self.ui.rbtMove2PointAfterZ.setChecked(self.__settings.value("Probe/go2PointZ", DEFAULT_PROBE_GO_2_POINT_AFTER_Z, type=bool))
        self.ui.rbtRetractAfterZ.setChecked(self.__settings.value("Probe/RetractAfterZ", DEFAULT_PROBE_RETRACT_AFTER_Z, type=bool))
        self.ui.dsbRetractZ.setValue(self.__settings.value("Probe/RetractDistanceZ", DEFAULT_PROBE_RETRACT_DISTANCE_AFTER_Z, type=float))
        self.ui.rbtDefineOriginZ_G54.setChecked(self.__settings.value("Probe/DefineOriginZ_G54", DEFAULT_PROBE_ORIGINE_G54_Z, type=bool))
        self.ui.rbtDefineOriginZ_G92.setChecked(self.__settings.value("Probe/DefineOriginZ_G92", DEFAULT_PROBE_ORIGINE_G92_Z, type=bool))
        self.ui.dsbOriginOffsetZ.setValue(self.__settings.value("Probe/OriginOffsetZ", DEFAULT_PROBE_ORIGINE_OFFSET_Z, type=float))
        self.ui.dsbToolLengthSensorZ.setValue(self.__settings.value("Probe/ToolChangePositionZ", DEFAULT_TOOLCHANGE_POSITION_Z, type=float))
        self.ui.dsbToolLengthSensorX.setValue(self.__settings.value("Probe/ToolChangePositionX", DEFAULT_TOOLCHANGE_POSITION_X, type=float))
        self.ui.dsbToolLengthSensorY.setValue(self.__settings.value("Probe/ToolChangePositionY", DEFAULT_TOOLCHANGE_POSITION_Y, type=float))
        # case a cocher invert probe pin
        if self.__decode.getGrblSetting(6) is not None:
          self.ui.chkInvertProbePinZ.setChecked((int(self.__decode.getGrblSetting(6)) == 1))


  @pyqtSlot()
  def on_btnProbeZ(self):
    ''' Z probing '''
    # Récupération des paramètres définis dans l'interface graphique
    probeDistance = self.ui.dsbDistanceZ.value()
    probeFeedRate = self.ui.dsbFeedRateZ.value()
    probeSeekRate = self.ui.dbsSeekRateZ.value()
    probePullOff  = self.ui.dsbPullOffZ.value()
    probeRetract  = self.ui.dsbRetractZ.value()
    doubleProbe   = self.ui.chkSeekZ.isChecked()
    if probeSeekRate < probeFeedRate:
      probeSeekRate = probeFeedRate
      self.ui.dbsSeekRateZ.setValue(probeSeekRate)

    # On mémorise le mode G90/G91 actif
    oldG90_91 = self.ui.lblCoord.text()
    if oldG90_91 != "G91":
      # On force le mode relatif
      self.__grblCom.gcodePush("G91")

    try:
      if doubleProbe:
        # Le probe se fait en 2 fois, dabord rapide à la vitesse probeSeekRate
        # puis plus lentement à la vitesse probeFeedRate.
        # On effectue le premier probe G38.3 (rapide)
        self.__probeResult = self.__probe.g38(P=3, F=probeSeekRate, Z=-probeDistance, g2p=False)
        # On mémorise le résultat
        self.ui.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
        self.__dlgToolChange.di.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
        # On retract d'une distance probePullOff
        retractGCode = "G0Z{:+0.3f}".format(probePullOff)
        self.__grblCom.gcodePush(retractGCode)
        # Pause pour laisser le temps à Grbl de lancer le mouvement de retract
        time.sleep(0.25)
        while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
          # Process events to receive signals en attendant que le GCode soit traité
          QCoreApplication.processEvents()
        # En cas de probe en 2 fois, le second probe ne nécessite que la distance de pull off
        fineProbeDistance = probePullOff
      else: # doubleProbe == False
        # En cas de probe en une fois, la distance à utiliser est probeDistance.
        fineProbeDistance = probeDistance

      # Si repositionnement après probe...
      if self.ui.gbMoveAfterZ.isChecked():
        # On aura au moins un retour au point précis,
        # donc, on le demande à la fonction self.__probe.g38()
        go2point = True
      else:
        go2point = False

      # On effectue le probe G38.3 précis
      self.__probeResult = self.__probe.g38(P=3, F=probeFeedRate, Z=-fineProbeDistance, g2p=go2point)
      # On mémorise le résultat précis
      self.ui.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))
      self.__dlgToolChange.di.lblLastProbZ.setText('{:+0.3f}'.format(float(self.__probeResult.getAxisByName("Z"))))

      if self.ui.rbtRetractAfterZ.isChecked():
        # On retract d'une distance probeRetract
        retractGCode = "G0Z{:+0.3f}".format(probeRetract)
        self.__grblCom.gcodePush(retractGCode)

    except ValueError as e:
      # Erreur arguments d'appel de self.__probe.g38()
      # L'axe demandé n'est pas dans la liste de self.__axisNames
      self.log(logSeverity.error.value, self.tr("on_btnProbeZ(): The requested axis ({}) is not in the axis list of this machine").format(e))
      pass

    except probeError as e:
      # Reception de OK, error ou alarm avant le résultat de probe
      self.log(logSeverity.error.value, self.tr("on_btnProbeZ(): {} no response from probe").format(e))
      pass

    except probeFailed as e:
      # Probe action terminée mais sans que la sonde ne touche
      self.log(logSeverity.error.value, self.tr("on_btnProbeZ(): {} Probe error").format(e))
      pass

    except speedError as e:
      # Vitesse F non définie, nulle ou négative
      self.log(logSeverity.error.value, self.tr("on_btnProbeZ(): F Speed undefined or less or equal to zero").format(e))
      pass
    
    if oldG90_91 != "G91":
      # On restore le mode relatif ou absolu
      self.__grblCom.gcodePush(oldG90_91)

    if (self.__probeResult is not None) and (self.__probeResult.isProbeOK()):
      self.__dlgToolChange.setInitialProbeZ(True)
      if self.__dlgToolChange.initialToolLenght():
        self.__dlgToolChange.calculateToolOffset()

    # Pour finir, on sauvegarde les derniers paramètres de probe dans les settings
    self.__settings.setValue("Probe/DistanceZ", self.ui.dsbDistanceZ.value())
    self.__settings.setValue("Probe/FeedRateZ", self.ui.dsbFeedRateZ.value())
    self.__settings.setValue("Probe/DoubleProbeZ", self.ui.chkSeekZ.isChecked())
    self.__settings.setValue("Probe/SeekRateZ", self.ui.dbsSeekRateZ.value())
    self.__settings.setValue("Probe/PullOffZ", self.ui.dsbPullOffZ.value())
    self.__settings.setValue("Probe/MoveAfterZ", self.ui.gbMoveAfterZ.isChecked())
    self.__settings.setValue("Probe/go2PointZ", self.ui.rbtMove2PointAfterZ.isChecked())
    self.__settings.setValue("Probe/RetractAfterZ", self.ui.rbtRetractAfterZ.isChecked())
    self.__settings.setValue("Probe/RetractDistanceZ", self.ui.dsbRetractZ.value())


  @pyqtSlot()
  def on_btnSaveToolChangePosition(self):
    '''
    Déplacement rapide du palpeur de longueur d'outil vers les coordonnées machine :
    Z d'abord pour dégager, puis X, Y.
    '''
    # Recupération des coordonnées Z, X & Y du point
    posZ = self.ui.dsbToolLengthSensorZ.value()
    posX = self.ui.dsbToolLengthSensorX.value()
    posY = self.ui.dsbToolLengthSensorY.value()
    # Memorise la position dans les settings
    self.__settings.setValue("Probe/ToolChangePositionZ", posZ)
    self.__settings.setValue("Probe/ToolChangePositionX", posX)
    self.__settings.setValue("Probe/ToolChangePositionY", posY)


  @pyqtSlot()
  def on_btnGoToSensor(self):
    '''
    Déplacement rapide du palpeur de longueur d'outil vers les coordonnées machine :
    Z d'abord pour dégager, puis X, Y.
    '''
    # Recupération des coordonnées Z, X & Y du point
    posZ = self.ui.dsbToolLengthSensorZ.value()
    posX = self.ui.dsbToolLengthSensorX.value()
    posY = self.ui.dsbToolLengthSensorY.value()
    # Effectue les déplacements
    deplacementGCodeZ  = "G53G0Z{}".format(posZ)
    deplacementGCodeXY = "G53G0X{}Y{}".format(posX, posY)
    self.__grblCom.gcodePush(deplacementGCodeZ)
    self.__grblCom.gcodePush(deplacementGCodeXY)
    # Memorise la position dans les settings
    self.__settings.setValue("Probe/ToolChangePositionZ", posZ)
    self.__settings.setValue("Probe/ToolChangePositionX", posX)
    self.__settings.setValue("Probe/ToolChangePositionY", posY)


  @pyqtSlot()
  def on_btnG49(self):
    ''' 
    Mémorise le Z du point de contact initial de l'outil pour calculer les outils suivants
    et envoi G49 pour réinitialiser une éventuelle longueur précédente.
    '''
    '''if not self.__dlgToolChange.__initialProbeZ:
      self.log(logSeverity.error.value, self.tr("on_btnG49(): No initial Z probe result, can't get initial tool length probe!"))
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
    
    # Initialise la longueur d'outil initiale
    self.ui.lblInitToolLength.setText(self.ui.lblLastProbZ.text())
    self.__dlgToolChange.di.lblInitToolLength.setText(self.__dlgToolChange.di.lblLastProbZ.text())
    self.__grblCom.gcodePush("G49")

    self.__dlgToolChange.__initialToolLenght = True
    '''
    self.__dlgToolChange.on_btnG49()

  @pyqtSlot()
  def on_btnG43_1(self):
    '''
    Calcul de la correction de longueur d'outil par rapport à la valeur initiale mémorisée
    et configure le "Tool Length Offset" dans Grbl à l'aide de G43.1
    '''
    '''if not self.__dlgToolChange.__initialToolLenght:
      self.log(logSeverity.error.value, self.tr("on_btnG43_1(): No initial tool length, can't calculate length offset!"))
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
    # Envoi de la correction de longueur d'outil
    toolOffset = self.__dlgToolChange.calculateToolOffset()
    toolOffsetGcode = "G43.1Z{}".format(toolOffset)
    self.__grblCom.gcodePush(toolOffsetGcode)
    '''
    self.__dlgToolChange.on_btnG43_1()


  @pyqtSlot()
  def on_btnSetOriginZ(self):
    '''
    Définit l'origine en Z en fonction du dernier palpage + offset
    '''
    # Dernier probe à prendre en compte
    lastProbe = float(self.ui.lblLastProbZ.text().replace(' ', ''))
    # Position machine actuelle en Z
    if self.ui.mnu_MPos.isChecked():
      # Affichage en position machine (MPos), c'est facile :)
      positionZ = float(self.ui.lblPosZ.text().replace(' ', ''))
    elif self.ui.mnu_WPos.isChecked():
      # Affichage en position de travail (WPos), on ajoute le décalage WCO.
      positionZ = float(self.ui.lblPosZ.text().replace(' ', '')) + float(self.ui.lblWcoZ.text().replace(' ', ''))
    # Offset à ajouter
    offsetZ = self.ui.dsbOriginOffsetZ.value()

    if self.ui.rbtDefineOriginZ_G54.isChecked():
      # Définit l'origine à l'aide du dégalage courant (G54 à G59)
      # Utilisation de G10L2P0Z<absolute Z> ne permet pas de composer avec G92...
      # donc, on utilise G10L20P0Z...
      newZoffset = positionZ - lastProbe + offsetZ
      originGcode = "G10L20P0Z{:+0.3f}".format(newZoffset)
    else: # rbtDefineOriginZ_G92.isChecked() = True
      newCurrentZ = positionZ - lastProbe + offsetZ
      originGcode = "G92Z{:+0.3f}".format(newCurrentZ)
    # Envoi du changement d'origine à Grbl
    self.__grblCom.gcodePush(originGcode)
    # Sauvegarde des derniers paramètres utilisés dans les settings
    self.__settings.setValue("Probe/DefineOriginZ_G54", self.ui.rbtDefineOriginZ_G54.isChecked())
    self.__settings.setValue("Probe/DefineOriginZ_G92", self.ui.rbtDefineOriginZ_G92.isChecked())
    self.__settings.setValue("Probe/OriginOffsetZ", self.ui.dsbOriginOffsetZ.value())


  @pyqtSlot()
  def on_chkSeekZ(self):
    if self.ui.chkSeekZ.isChecked():
      self.ui.dbsSeekRateZ.setEnabled(True)
      self.ui.lblPullOffZ.setEnabled(True)
      self.ui.dsbPullOffZ.setEnabled(True)
    else:
      self.ui.dbsSeekRateZ.setEnabled(False)
      self.ui.lblPullOffZ.setEnabled(False)
      self.ui.dsbPullOffZ.setEnabled(False)


  @pyqtSlot(float)
  def on_dsbToolDiameterValueChanged(self, newVal):
    self.ui.dsbOriginOffsetX.setValue(newVal/2)
    self.ui.dsbOriginOffsetY.setValue(newVal/2)


  @pyqtSlot(int)
  def on_chkAddOffsetXstateChanged(self, newVal):
    self.ui.dsbOriginOffsetX.setEnabled(True if newVal != 0 else False)


  @pyqtSlot(int)
  def on_chkAddOffsetYstateChanged(self, newVal):
    self.ui.dsbOriginOffsetY.setEnabled(True if newVal != 0 else False)


  def resetProbeResults(self):
    # Remise à 0 des résultats probe XY en gris
    self.ui.qfProbeResultXmax.setText("+0000.000")
    self.ui.qfProbeResultXmax.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultYmax.setText("+0000.000")
    self.ui.qfProbeResultYmax.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultXcenter.setText("+0000.000")
    self.ui.qfProbeResultXcenter.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultYcenter.setText("+0000.000")
    self.ui.qfProbeResultYcenter.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultXmin.setText("+0000.000")
    self.ui.qfProbeResultXmin.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultYmin.setText("+0000.000")
    self.ui.qfProbeResultYmin.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultXlength.setText("+0000.000")
    self.ui.qfProbeResultXlength.setStyleSheet("color: #808080;")
    self.ui.qfProbeResultYlength.setText("+0000.000")
    self.ui.qfProbeResultYlength.setStyleSheet("color: #808080;")
    # flag pour mise à jour de l'interface résultats probe XY et valeurs de calcul de centre
    self.__xMin      = False
    self.__xMinValue = None
    self.__xMax      = False
    self.__xMaxValue = None
    self.__yMin      = False
    self.__yMinValue = None
    self.__yMax      = False
    self.__yMaxValue = None
    # Desactivation des boutons de définition origine
    self.ui.btnHomeCenterX.setEnabled(False)
    self.ui.btnHomeCenterXY.setEnabled(False)
    self.ui.btnHomeCenterY.setEnabled(False)
    self.ui.btnHomeMoinsX.setEnabled(False)
    self.ui.btnHomeMoinsY.setEnabled(False)
    self.ui.btnHomePlusX.setEnabled(False)
    self.ui.btnHomePlusY.setEnabled(False)
    # Desactivation des offsets
    self.ui.chkAddOffsetX.setChecked(False)
    self.ui.chkAddOffsetY.setChecked(False)


  def on_btnProbeXY(self, btnNum: int):
    ''' Déclenchement du probe X ou Y en fonction du bouton et du sens inside ou outside '''

    # Récupération des paramètres définis dans l'interface graphique
    probeInside    = self.ui.rbtProbeInsideXY.isChecked()
    probeOutside   = self.ui.rbtProbeOutsideXY.isChecked()
    toolDiameter   = self.ui.dsbToolDiameter.value()
    probeDistance  = self.ui.dsbDistanceXY.value()
    clearanceXY    = self.ui.dsbClearanceXY.value()
    clearanceZ     = self.ui.dsbClearanceZ.value()
    feedRateXY     = self.ui.dsbFeedRateXY.value()
    doubleProbeXY  = self.ui.chkSeekXY.isChecked()
    seekRateXY     = self.ui.dbsSeekRateXY.value()
    if seekRateXY < feedRateXY:
      seekRateXY = feedRateXY
      self.ui.dbsSeekRateXY.setValue(seekRateXY)
    pullOffXY      = self.ui.dsbPullOffXY.value()
    moveAfterXY    = self.ui.gbMoveAfterXY.isChecked()
    go2pointXY     = self.ui.rbtMove2PointAfterXY.isChecked()
    retractAfterXY = self.ui.rbtRetractAfterXY.isChecked()
    retractXY      = self.ui.dsbRetractXY.value()

    # On mémorise le mode G90/G91 actif
    oldG90_91 = self.ui.lblCoord.text()
    if oldG90_91 != "G91":
      # On force le mode de déplacement relatif
      self.__grblCom.gcodePush("G91")

    def probeXplus(length = probeDistance):
      if doubleProbeXY:
        pr = self.__probe.g38(P=3, F=seekRateXY, X=length, g2p=False)
        if probeInside:
          self.__xMaxValue = float(pr.getAxisByName("X"))
          self.ui.qfProbeResultXmax.setText('{:+0.3f}'.format(self.__xMaxValue))
          self.ui.qfProbeResultXmax.setStyleSheet("color: #000020;")
          self.__xMax = True
        else:
          self.__xMinValue = float(pr.getAxisByName("X"))
          self.ui.qfProbeResultXmin.setText('{:+0.3f}'.format(self.__xMinValue))
          self.ui.qfProbeResultXmin.setStyleSheet("color: #000020;")
          self.__xMin = True
        self.calculateCenterXY()
        self.__grblCom.gcodePush("G0X{}".format(-pullOffXY))
        time.sleep(0.25)
        while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
          QCoreApplication.processEvents()
        fineProbeDistance = pullOffXY
      else:
        fineProbeDistance = length
      if self.ui.gbMoveAfterXY.isChecked():
        go2point = True
      else:
        go2point = False
      pr = self.__probe.g38(P=3, F=feedRateXY, X=fineProbeDistance, g2p=go2point)
      if probeInside:
        self.__xMaxValue = float(pr.getAxisByName("X"))
        self.ui.qfProbeResultXmax.setText('{:+0.3f}'.format(self.__xMaxValue))
        self.ui.qfProbeResultXmax.setStyleSheet("color: #000020;")
        self.__xMax = True
      else:
        self.__xMinValue = float(pr.getAxisByName("X"))
        self.ui.qfProbeResultXmin.setText('{:+0.3f}'.format(self.__xMinValue))
        self.ui.qfProbeResultXmin.setStyleSheet("color: #000020;")
        self.__xMin = True
      self.calculateCenterXY()
    
    def probeXmoins(length = probeDistance):
      if doubleProbeXY:
        pr = self.__probe.g38(P=3, F=seekRateXY, X=-length, g2p=False)
        if probeInside:
          self.__xMinValue = float(pr.getAxisByName("X"))
          self.ui.qfProbeResultXmin.setText('{:+0.3f}'.format(self.__xMinValue))
          self.ui.qfProbeResultXmin.setStyleSheet("color: #000020;")
          self.__xMin = True
        else:
          self.__xMaxValue = float(pr.getAxisByName("X"))
          self.ui.qfProbeResultXmax.setText('{:+0.3f}'.format(self.__xMaxValue))
          self.ui.qfProbeResultXmax.setStyleSheet("color: #000020;")
          self.__xMax = True
        self.calculateCenterXY()
        self.__grblCom.gcodePush("G0X{}".format(pullOffXY))
        time.sleep(0.25)
        while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
          QCoreApplication.processEvents()
        fineProbeDistance = pullOffXY
      else:
        fineProbeDistance = length
      if self.ui.gbMoveAfterXY.isChecked():
        go2point = True
      else:
        go2point = False
      pr = self.__probe.g38(P=3, F=feedRateXY, X=-fineProbeDistance, g2p=go2point)
      if probeInside:
        self.__xMinValue = float(pr.getAxisByName("X"))
        self.ui.qfProbeResultXmin.setText('{:+0.3f}'.format(self.__xMinValue))
        self.ui.qfProbeResultXmin.setStyleSheet("color: #000020;")
        self.__xMin = True
      else:
        self.__xMaxValue = float(pr.getAxisByName("X"))
        self.ui.qfProbeResultXmax.setText('{:+0.3f}'.format(self.__xMaxValue))
        self.ui.qfProbeResultXmax.setStyleSheet("color: #000020;")
        self.__xMax = True
      self.calculateCenterXY()

    def probeYplus(length = probeDistance):
      if doubleProbeXY:
        pr = self.__probe.g38(P=3, F=seekRateXY, Y=length, g2p=False)
        if probeInside:
          self.__yMaxValue = float(pr.getAxisByName("Y"))
          self.ui.qfProbeResultYmax.setText('{:+0.3f}'.format(self.__yMaxValue))
          self.ui.qfProbeResultYmax.setStyleSheet("color: #000020;")
          self.__yMax = True
        else:
          self.__yMinValue = float(pr.getAxisByName("Y"))
          self.ui.qfProbeResultYmin.setText('{:+0.3f}'.format(self.__yMinValue))
          self.ui.qfProbeResultYmin.setStyleSheet("color: #000020;")
          self.__yMin = True
        self.calculateCenterXY()
        self.__grblCom.gcodePush("G0Y{}".format(-pullOffXY))
        time.sleep(0.25)
        while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
          QCoreApplication.processEvents()
        fineProbeDistance = pullOffXY
      else:
        fineProbeDistance = length
      if self.ui.gbMoveAfterXY.isChecked():
        go2point = True
      else:
        go2point = False
      pr = self.__probe.g38(P=3, F=feedRateXY, Y=fineProbeDistance, g2p=go2point)
      if probeInside:
        self.__yMaxValue = float(pr.getAxisByName("Y"))
        self.ui.qfProbeResultYmax.setText('{:+0.3f}'.format(self.__yMaxValue))
        self.ui.qfProbeResultYmax.setStyleSheet("color: #000020;")
        self.__yMax = True
      else:
        self.__yMinValue = float(pr.getAxisByName("Y"))
        self.ui.qfProbeResultYmin.setText('{:+0.3f}'.format(self.__yMinValue))
        self.ui.qfProbeResultYmin.setStyleSheet("color: #000020;")
        self.__yMin = True
      self.calculateCenterXY()

    def probeYmoins(length = probeDistance):
      if doubleProbeXY:
        pr = self.__probe.g38(P=3, F=seekRateXY, Y=-length, g2p=False)
        if probeInside:
          self.__yMinValue = float(pr.getAxisByName("Y"))
          self.ui.qfProbeResultYmin.setText('{:+0.3f}'.format(self.__yMinValue))
          self.ui.qfProbeResultYmin.setStyleSheet("color: #000020;")
          self.__yMin = True
        else:
          self.__yMaxValue = float(pr.getAxisByName("Y"))
          self.ui.qfProbeResultYmax.setText('{:+0.3f}'.format(self.__yMaxValue))
          self.ui.qfProbeResultYmax.setStyleSheet("color: #000020;")
          self.__yMax = True
        self.calculateCenterXY()
        self.__grblCom.gcodePush("G0Y{}".format(pullOffXY))
        time.sleep(0.25)
        while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
          QCoreApplication.processEvents()
        fineProbeDistance = pullOffXY
      else:
        fineProbeDistance = length
      if self.ui.gbMoveAfterXY.isChecked():
        go2point = True
      else:
        go2point = False
      pr = self.__probe.g38(P=3, F=feedRateXY, Y=-fineProbeDistance, g2p=go2point)
      if probeInside:
        self.__yMinValue = float(pr.getAxisByName("Y"))
        self.ui.qfProbeResultYmin.setText('{:+0.3f}'.format(self.__yMinValue))
        self.ui.qfProbeResultYmin.setStyleSheet("color: #000020;")
        self.__yMin = True
      else:
        self.__yMaxValue = float(pr.getAxisByName("Y"))
        self.ui.qfProbeResultYmax.setText('{:+0.3f}'.format(self.__yMaxValue))
        self.ui.qfProbeResultYmax.setStyleSheet("color: #000020;")
        self.__yMax = True
      self.calculateCenterXY()

    try:

      if btnNum == 4 and probeInside \
      or btnNum == 8 and probeOutside: # inside X+, outside X+
        probeXplus()
        if retractAfterXY:
          self.__grblCom.gcodePush("G0X{}".format(-retractXY))
        self.ui.chkAddOffsetX.setChecked(True)

      elif btnNum == 8 and probeInside \
      or   btnNum == 4 and probeOutside: # inside X-, outside X-
        probeXmoins()
        if retractAfterXY:
          self.__grblCom.gcodePush("G0X{}".format(retractXY))
        self.ui.chkAddOffsetX.setChecked(True)

      elif btnNum == 2 and probeInside \
      or   btnNum == 6 and probeOutside: # inside Y+, outside Y+
        probeYplus()
        if retractAfterXY:
          self.__grblCom.gcodePush("G0Y{}".format(-retractXY))
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 6 and probeInside \
      or   btnNum == 2 and probeOutside: # inside Y-, outside Y-
        probeYmoins()
        if retractAfterXY:
          self.__grblCom.gcodePush("G0Y{}".format(retractXY))
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 3 and probeInside: # inside corner X+, Y+
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-clearanceXY, -probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXplus(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY - probeDistance + (toolDiameter / 2), probeDistance - clearanceXY))
        probeYplus(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance, clearanceXY + (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 5 and probeInside: # inside corner  X+, Y-
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-clearanceXY, probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXplus(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY - probeDistance + (toolDiameter / 2), -probeDistance + clearanceXY))
        probeYmoins(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance, -clearanceXY - (toolDiameter / 2)))        
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 7 and probeInside: # inside corner  X-, Y-
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY, probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXmoins(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance - clearanceXY - (toolDiameter / 2), -probeDistance + clearanceXY))
        probeYmoins(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance, -clearanceXY - (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 1 and probeInside: # inside corner  X-, Y+
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY, -probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXmoins(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance - clearanceXY- (toolDiameter / 2), probeDistance - clearanceXY))
        probeYplus(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance, clearanceXY + (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 7 and probeOutside: # outside corner X+, Y+
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-clearanceXY, probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXplus(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance + clearanceXY + (toolDiameter / 2), -probeDistance - clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYplus(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance, clearanceXY + (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 1 and probeOutside: # outside corner  X+, Y-
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-clearanceXY, -probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXplus(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance + clearanceXY + (toolDiameter / 2), +probeDistance + clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYmoins(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance, -clearanceXY - (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif  btnNum == 3 and probeOutside: # outside corner  X-, Y-
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY, -probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXmoins(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance - clearanceXY - (toolDiameter / 2), +probeDistance + clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYmoins(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance, -clearanceXY - (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif   btnNum == 5 and probeOutside: # outside corner  X-, Y+
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(clearanceXY, probeDistance))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXmoins(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(-probeDistance - clearanceXY - (toolDiameter / 2), -probeDistance - clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYplus(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}Y{:+0.3f}".format(probeDistance, clearanceXY + (toolDiameter / 2)))
        self.ui.chkAddOffsetX.setChecked(True)
        self.ui.chkAddOffsetY.setChecked(True)

      elif btnNum == 0 and probeInside: # inside Full center 
        # On commence par réinitialiser les résultats
        self.resetProbeResults
        self.ui.chkAddOffsetX.setChecked(False)
        self.ui.chkAddOffsetY.setChecked(False)
        # Puis, on bouge
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-probeDistance + clearanceXY))
        probeXmoins(clearanceXY)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format((2 * probeDistance) - clearanceXY - (toolDiameter / 2)))
        probeXplus(clearanceXY)
        # Calcule et se deplace au centre en X
        centreX = (self.__xMinValue + self.__xMaxValue) / 2
        self.__grblCom.gcodePush("G53G0X{:+0.3f}".format(centreX))
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-probeDistance + clearanceXY))
        probeYmoins(clearanceXY)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format((2 * probeDistance) - clearanceXY - (toolDiameter / 2)))
        probeYplus(clearanceXY)
        # Calcule et se deplace au centre en Y
        centreY = (self.__yMinValue + self.__yMaxValue) / 2
        self.__grblCom.gcodePush("G53G0Y{:+0.3f}".format(centreY))
        # Remonte et c'est fini :-)
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))

      elif btnNum == 0 and probeOutside: # outside Full center 
        # On commence par réinitialiser les résultats
        self.resetProbeResults
        self.ui.chkAddOffsetX.setChecked(False)
        self.ui.chkAddOffsetY.setChecked(False)
        # Probe en X+ / X-
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-probeDistance - clearanceXY - (toolDiameter/2)))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXplus((clearanceXY * 2) + toolDiameter)
        time.sleep(0.25)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(2 * (probeDistance + clearanceXY) + toolDiameter))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeXmoins((clearanceXY * 2) + toolDiameter)
        time.sleep(0.25)
        self.__grblCom.gcodePush("G0X{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        # Calcule et se deplace au centre en X
        centreX = (self.__xMinValue + self.__xMaxValue) / 2
        self.__grblCom.gcodePush("G53G0X{:+0.3f}".format(centreX))
        # Probe en Y+ / Y-
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-probeDistance - clearanceXY - (toolDiameter/2)))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYplus((clearanceXY * 2) + toolDiameter)
        time.sleep(0.25)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(-clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(2 * (probeDistance + clearanceXY) + toolDiameter))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(-clearanceZ))
        probeYmoins((clearanceXY * 2) + toolDiameter)
        time.sleep(0.25)
        self.__grblCom.gcodePush("G0Y{:+0.3f}".format(clearanceXY))
        self.__grblCom.gcodePush("G0Z{:+0.3f}".format(clearanceZ))
        # Calcule et se deplace au centre en Y
        centreY = (self.__yMinValue + self.__yMaxValue) / 2
        self.__grblCom.gcodePush("G53G0Y{:+0.3f}".format(centreY))

    except ValueError as e:
      # Erreur arguments d'appel de self.__probe.g38()
      # L'axe demandé n'est pas dans la liste de self.__axisNames
      self.log(logSeverity.error.value, self.tr("on_btnProbeXY(): The requested axis ({}) is not in the axis list of this machine").format(e))
      pass

    except probeError as e:
      # Reception de OK, error ou alarm avant le résultat de probe
      self.log(logSeverity.error.value, self.tr("on_btnProbeXY(): {} no response from probe").format(e))
      pass

    except probeFailed as e:
      # Probe action terminée mais sans que la sonde ne touche
      self.log(logSeverity.error.value, self.tr("on_btnProbeXY(): {} Probe error").format(e))
      pass

    except speedError as e:
      # Vitesse F non définie, nulle ou négative
      self.log(logSeverity.error.value, self.tr("on_btnProbeXY(): F Speed undefined or less or equal to zero").format(e))
      pass
    
    if oldG90_91 != "G91":
      # On restore le mode relatif ou absolu
      self.__grblCom.gcodePush(oldG90_91)

    # Pour finir, on sauvegarde les derniers paramètres de probe dans les settings
    self.__settings.setValue("Probe/ToolDiameter", self.ui.dsbToolDiameter.value())
    self.__settings.setValue("Probe/DistanceXY", self.ui.dsbDistanceXY.value())
    self.__settings.setValue("Probe/ClearanceXY", self.ui.dsbClearanceXY.value())
    self.__settings.setValue("Probe/ClearanceZ", self.ui.dsbClearanceZ.value())
    self.__settings.setValue("Probe/FeedRateXY", self.ui.dsbFeedRateXY.value())
    self.__settings.setValue("Probe/DoubleProbeXY", self.ui.chkSeekXY.isChecked())
    self.__settings.setValue("Probe/SeekRateXY", self.ui.dbsSeekRateXY.value())
    self.__settings.setValue("Probe/PullOffXY", self.ui.dsbPullOffXY.value())
    self.__settings.setValue("Probe/MoveAfterXY", self.ui.gbMoveAfterXY.isChecked())
    self.__settings.setValue("Probe/go2PointXY", self.ui.rbtMove2PointAfterXY.isChecked())
    self.__settings.setValue("Probe/RetractAfterXY", self.ui.rbtRetractAfterXY.isChecked())
    self.__settings.setValue("Probe/RetractDistanceXY", self.ui.dsbRetractXY.value())


  def calculateCenterXY(self):
    if self.__xMin and self.__xMax:
      self.ui.qfProbeResultXcenter.setText('{:+0.3f}'.format((float(self.ui.qfProbeResultXmax.text())+float(self.ui.qfProbeResultXmin.text()))/2))
      self.ui.qfProbeResultXcenter.setStyleSheet("color: #000020;")
      self.ui.qfProbeResultXlength.setText('{:+0.3f}'.format(float(self.ui.qfProbeResultXmax.text())-float(self.ui.qfProbeResultXmin.text())))
      self.ui.qfProbeResultXlength.setStyleSheet("color: #000020;")
      self.ui.btnHomeCenterX.setEnabled(True)
    if self.__yMin and self.__yMax:
      self.ui.qfProbeResultYcenter.setText('{:+0.3f}'.format((float(self.ui.qfProbeResultYmax.text())+float(self.ui.qfProbeResultYmin.text()))/2))
      self.ui.qfProbeResultYcenter.setStyleSheet("color: #000020;")
      self.ui.qfProbeResultYlength.setText('{:+0.3f}'.format(float(self.ui.qfProbeResultYmax.text())-float(self.ui.qfProbeResultYmin.text())))
      self.ui.qfProbeResultYlength.setStyleSheet("color: #000020;")
      self.ui.btnHomeCenterY.setEnabled(True)
    if self.__xMin:
      self.ui.btnHomeMoinsX.setEnabled(True)
    if self.__xMax:
      self.ui.btnHomePlusX.setEnabled(True)
    if self.__yMin:
      self.ui.btnHomeMoinsY.setEnabled(True)
    if self.__yMax:
      self.ui.btnHomePlusY.setEnabled(True)
    if self.__xMin and self.__xMax and self.__yMin and self.__yMax:
      self.ui.btnHomeCenterXY.setEnabled(True)


  def on_btnHomeXY(self, action: str):
    ''' XY Origin definition '''
    
    # Récupération des paramètres définis dans l'interface graphique
    addOffsetX = self.ui.chkAddOffsetX.isChecked()
    offsetX    = self.ui.dsbOriginOffsetX.value()
    addOffsetY = self.ui.chkAddOffsetY.isChecked()
    offsetY    = self.ui.dsbOriginOffsetY.value()

    if  action == "moinsX":
      position = self.__decode.getMpos('X')
      probe    = float(self.ui.qfProbeResultXmin.text().replace(' ', ''))
      offset    = offsetX if addOffsetX else 0
      valeur = position - probe - offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0X{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92X{:+0.3f}".format(valeur)

    elif action == "moinsY":
      position = self.__decode.getMpos('Y')
      probe    = float(self.ui.qfProbeResultYmin.text().replace(' ', ''))
      offset    = offsetY if addOffsetY else 0
      valeur = position - probe - offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0Y{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92Y{:+0.3f}".format(valeur)

    elif action == "plusX":
      position = self.__decode.getMpos('X')
      probe    = float(self.ui.qfProbeResultXmax.text().replace(' ', ''))
      offset    = offsetX if addOffsetX else 0
      valeur = position - probe + offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0X{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92X{:+0.3f}".format(valeur)

    elif action == "plusY":
      position = self.__decode.getMpos('Y')
      probe    = float(self.ui.qfProbeResultYmax.text().replace(' ', ''))
      offset    = offsetY if addOffsetY else 0
      valeur = position - probe + offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0Y{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92Y{:+0.3f}".format(valeur)

    elif action == "centerX":
      position = self.__decode.getMpos('X')
      probe    = float(self.ui.qfProbeResultXcenter.text().replace(' ', ''))
      offset    = offsetX if addOffsetX else 0
      valeur = position - probe + offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0X{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92X{:+0.3f}".format(valeur)

    elif action == "centerY":
      position = self.__decode.getMpos('Y')
      probe    = float(self.ui.qfProbeResultYcenter.text().replace(' ', ''))
      offset    = offsetY if addOffsetY else 0
      valeur = position - probe - offset
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0Y{:+0.3f}".format(valeur)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92Y{:+0.3f}".format(valeur)

    elif action == "centerXY":
      positionX = self.__decode.getMpos('X')
      probeX    = float(self.ui.qfProbeResultXcenter.text().replace(' ', ''))
      offsetX   = offsetX if addOffsetX else 0
      valeurX   = positionX - probeX - offsetX
      positionY = self.__decode.getMpos('Y')
      probeY    = float(self.ui.qfProbeResultYcenter.text().replace(' ', ''))
      offsetY   = offsetY if addOffsetY else 0
      valeurY   = positionY - probeY - offsetY
      if self.ui.rbtDefineOriginXY_G54.isChecked():
        originGcode = "G10L20P0X{:+0.3f}Y{:+0.3f}".format(valeurX, valeurY)
      else: # rbtDefineOriginZ_G92.isChecked() = True
        originGcode = "G92X{:+0.3f}Y{:+0.3f}".format(valeurX, valeurY)

    self.__grblCom.gcodePush(originGcode)


  @pyqtSlot()
  def on_chkSeekXY(self):
    if self.ui.chkSeekXY.isChecked():
      self.ui.dbsSeekRateXY.setEnabled(True)
      self.ui.lblPullOffXY.setEnabled(True)
      self.ui.dsbPullOffXY.setEnabled(True)
    else:
      self.ui.dbsSeekRateXY.setEnabled(False)
      self.ui.lblPullOffXY.setEnabled(False)
      self.ui.dsbPullOffXY.setEnabled(False)


  @pyqtSlot()
  def on_chkInvertProbePinZ(self):
    if self.ui.chkInvertProbePinZ.isChecked():
      self.__grblCom.gcodePush("$6=1")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)
    else:
      self.__grblCom.gcodePush("$6=0")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)


  @pyqtSlot()
  def on_chkInvertProbePinXY(self):
    if self.ui.chkInvertProbePinXY.isChecked():
      self.__grblCom.gcodePush("$6=1")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)
    else:
      self.__grblCom.gcodePush("$6=0")
      self.__grblCom.gcodePush(CMD_GRBL_GET_SETTINGS)


  @pyqtSlot(str)
  def on_sig_config_changed(self, data: str):
    self.log(logSeverity.info.value, self.tr("Grbl configuration updated: {}").format(data))


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
        self.log(logSeverity.info.value, self.tr("Unlocking emergency stop."))
    else:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
      self.__arretUrgence = True
      self.log(logSeverity.warning.value, self.tr("Emergency stop pressed: STOP !!!"))

    # Actualise l'etat actif/inactif des groupes de controles de pilotage de Grbl
    self.setEnableDisableGroupes()


  @pyqtSlot()
  def action_btnConnect(self):
    if not self.__connectionStatus:
      # Force l'onglet "Grbl output" sauf en cas de debug
      if not self.ui.btnDebug.isChecked():
        self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_GRBL)
      # Recupere les coordonnees et parametres du port a connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      baudRate = int(self.ui.cmbBauds.currentText())
      # Demarrage du communicator
      self.__grblCom.startCom(serialDevice, baudRate)
      # Mémorise le dernier port série utilisé
      self.__settings.setValue("grblDevice", serialDevice)
    else:
      # Arret du comunicator
      self.__grblCom.stopCom()
      self.__connectionStatus = self.__grblCom.isOpen()
      self.ui.btnConnect.setText(self.tr("Connect")) # La prochaine action du bouton sera pour connecter
      # Force l'onglet "log" sauf en cas de debug
      if not self.ui.btnDebug.isChecked():
        self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)


  @pyqtSlot()
  def on_sig_connect(self):
    self.__connectionStatus = self.__grblCom.isOpen()
    if self.__connectionStatus:
      # Mise a jour de l'interface machine connectée
      self.ui.lblConnectStatus.setText(self.tr("Connected to {}").format(self.ui.cmbPort.currentText().split("-")[0].strip()))
      self.ui.btnConnect.setText(self.tr("Disconnect")) # La prochaine action du bouton sera pour deconnecter
      self.setEnableDisableConnectControls()
      # Active les groupes de controles de pilotage de Grbl
      self.setEnableDisableGroupes()
      self.ui.lblSerialLock.setStyleSheet(".QLabel{border-radius: 3px; background: green;}")
      self.ui.lblSerialActivity.setStyleSheet(".QLabel{border-radius: 3px; background: green;}")
      # Beep
      self.__beeper.beep(1760, 0.25, 16000)

    else:
      # Mise a jour de l'interface machine non connectée
      self.ui.lblConnectStatus.setText(self.tr("<Not Connected>"))
      self.ui.btnConnect.setText(self.tr("Connect")) # La prochaine action du bouton sera pour connecter
      self.__statusText = ""
      self.ui.statusBar.showMessage(self.__statusText)
      self.setEnableDisableConnectControls()
      self.ui.lblSerialLock.setStyleSheet(".QLabel{border-radius: 3px; background: #35322f;}")
      self.ui.lblSerialActivity.setStyleSheet(".QLabel{border-radius: 3px; background: #35322f;}")
      # Force la position de l'arret d'urgence
      self.__arretUrgence = True
      # Active les groupes de controles de pilotage de Grbl
      self.setEnableDisableGroupes()
      # On redemandera les paramètres à la prochaine connection
      self.__firstGetSettings = False


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
    if (self.ui.btnLinkOverride.isChecked()):
      self.ui.btnLinkOverride.setIcon(self.iconLinkOn)
      if (self.ui.dialAvance.value() != self.ui.dialBroche.value()):
        # On force comme valeur la moyenne des 2
        newValue = int((self.ui.dialAvance.value() + self.ui.dialBroche.value()) / 2)
        self.ui.dialBroche.setValue(newValue)
        self.ui.dialAvance.setValue(newValue)
    else: # Bouton non checked
      self.ui.btnLinkOverride.setIcon(self.iconLinkOff)


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
    # Jogging seulement si Idle
    if self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
      return

    # On anticipe l'état GRBL_STATUS_JOG
    self.__decode.set_etatMachine(GRBL_STATUS_JOG)

    jogDistance = 0
    for qrb in [self.ui.rbtJog0000, self.ui.rbtJog0001, self.ui.rbtJog0010, self.ui.rbtJog0100, self.ui.rbtJog1000]:
      if qrb.isChecked():
        jogDistance = float(qrb.text().replace(' ', ''))

    if jogDistance != 0:
      self.__jogModContinue = False
      while cnButton.isMouseDown():  # on envoi qu'après avoir relâché le bouton
        # Process events to receive signals en attendant que le bouton soit relâché;
        QCoreApplication.processEvents()
      # envoi de l'ordre jog
      self.__jog.on_jog(cnButton, e, jogDistance)

    else:  # jogDistance == 0
      self.__jogModContinue = True
      # Recherche la course max de l'axe considéré
      axis = cnButton.name()[-1]   # L'axe est definit par le dernier caractere du nom du Bouton
      maxTravel = 0
      for I in range(self.__nbAxis):
        if axis == self.__axisNames[I]:
          maxTravel = self.__maxTravel[I]
          break
      # envoi de l'ordre jog
      self.__jog.on_jog(cnButton, e, jogDistance, maxTravel)


  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent)
  def stop_jog(self, cnButton, e):
    if self.__jogModContinue:
      self.__jog.jogCancel()


  @pyqtSlot(float)
  def on_dsbJogSpeed_valueChanged(self, val: float):
    self.__jog.setJogSpeed(val)


  @pyqtSlot(int)
  def on_btnM64(self, digitNum: int):
    if self.__decode.getDigitalStatus(digitNum):
      self.__grblCom.gcodePush("M65P{}".format(digitNum))
    else:
      self.__grblCom.gcodePush("M64P{}".format(digitNum))


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
    if self.__decode.get_etatArrosage() != "M7" and self.__decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)


  @pyqtSlot()
  def on_btnFloodM8(self):
    if self.__decode.get_etatArrosage() != "M8" and self.__decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot()
  def on_btnFloodM9(self):
    if self.__decode.get_etatArrosage() == "M7" or self.__decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_MIST_COOLANT)
    if self.__decode.get_etatArrosage() == "M8" or self.__decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      self.__grblCom.realTimePush(REAL_TIME_TOGGLE_FLOOD_COOLANT)


  @pyqtSlot(str, QtGui.QMouseEvent)
  def on_lblG5xClick(self, lblText, e):
    self.__grblCom.gcodePush(lblText)


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
  def showKeyboard(self):
    if not self.__qwKeyboard.isVisible():
      self.__qwKeyboard.keyboard_show()
      self.ui.txtGCode.setFocus()
      self.ui.txtGCode.selectAll()
      self.ui.btnKeyboard.setText("⇩⌨⇩")
    else:
      self.__qwKeyboard.keyboard_hide()
      self.ui.txtGCode.setFocus()
      self.ui.txtGCode.selectAll()
      self.ui.btnKeyboard.setText("⇧⌨⇧")


  @pyqtSlot()
  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      if self.ui.txtGCode.text() == REAL_TIME_REPORT_QUERY:
        self.__decode.getNextStatus()
      if self.ui.txtGCode.text() == CMD_GRBL_GET_GCODE_PARAMATERS:
        self.__decode.getNextGCodeParams()
      if self.ui.txtGCode.text() == CMD_GRBL_GET_GCODE_STATE:
        self.__decode.getNextGCodeState()
      if "G38" in self.ui.txtGCode.text():
        self.__decode.getNextProbe()
      self.__grblCom.gcodePush(self.ui.txtGCode.text())
    else:
      self.__grblCom.realTimePush("\r\n")
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
      self.__decode.getNextStatus()
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
        self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)
    elif severity == logSeverity.error.value:
      self.logCn5X.setTextColor(TXT_COLOR_RED)
      self.logCn5X.append(time.strftime("%Y-%m-%d %H:%M:%S") + " : Error   : " + data)
      if not self.ui.btnDebug.isChecked():
        self.ui.qtabConsole.setCurrentIndex(CN5X_TAB_LOG)


  def log(self, severity: int, data: str):
    self.on_sig_log(severity, data)


  @pyqtSlot(str)
  def on_sig_init(self, data: str):
    self.log(logSeverity.info.value, self.tr("cn5X++ : Grbl initialized."))
    self.logGrbl.append(data)
    self.__statusText = data.split("[")[0]
    self.ui.statusBar.showMessage(self.__statusText)
    # Interroge la config de grbl si la première fois
    if not self.__firstGetSettings:
      self.__grblCom.gcodeInsert(CMD_GRBL_GET_SETTINGS)
      self.__firstGetSettings = True
    # Relis les paramètres GCodes
    self.__grblCom.gcodeInsert(CMD_GRBL_GET_GCODE_PARAMATERS)


  @pyqtSlot()
  def on_sig_ok(self):
    self.logGrbl.append("ok")


  @pyqtSlot(int)
  def on_sig_error(self, errNum: int):
    self.logGrbl.append(self.__decode.errorMessage(errNum))
    if self.__cycleRun:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__cycleRun = False
      self.__cyclePause = False
      # Masque de la boite de progression
      if self.__pBox.isVisible():
        if self.__pBox.autoClose():
          self.__pBox.stop()
        else:
          self.__pBox.enableClose()


  @pyqtSlot(int)
  def on_sig_alarm(self, alarmNum: int):
    self.logGrbl.append(self.__decode.alarmMessage(alarmNum))
    self.__decode.set_etatMachine(GRBL_STATUS_ALARM)
    if self.__cycleRun:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__cycleRun = False
      self.__cyclePause = False
      # Masque de la boite de progression
      if self.__pBox.isVisible():
        if self.__pBox.autoClose():
          self.__pBox.stop()
        else:
          self.__pBox.enableClose()


  @pyqtSlot(str)
  def on_sig_status(self, data: str):
    retour = self.__decode.decodeGrblStatus(data)
    if retour != "":
      self.logGrbl.append(retour)


  @pyqtSlot(str)
  def on_sig_data(self, data: str):
    retour = self.__decode.decodeGrblData(data)
    if retour is not None and retour != "":
      self.logGrbl.append(retour)


  @pyqtSlot(str)
  def on_sig_config(self, data: str):
    # Repere la chaine "[AXS:5:XYZABCUVW]" pour recuperer le nombre d'axes et leurs noms
    if data[:5] == "[AXS:":
      self.__nbAxis           = int(data[1:-1].split(':')[1])
      self.__axisNames        = list(data[1:-1].split(':')[2])
      # Mise à jour classe grblProbe
      self.__probe.setAxisNames(self.__axisNames)
      # Mise à jour classe dlgToolChange
      self.__dlgToolChange.setAxisNumber(self.__nbAxis)
      self.__dlgToolChange.setAxisNames(self.__axisNames)
      if len(self.__axisNames) < self.__nbAxis:
        # Il est posible qu'il y ait moins de lettres que le nombre d'axes si Grbl
        # implémente l'option REPORT_VALUE_FOR_AXIS_NAME_ONCE
        self.__nbAxis = len(self.__axisNames);
      
    # Memorise les courses maxi pour calcul des jogs max.
    elif data[:4] == "$130":
      self.__maxTravel[0] = float(data[5:])
    elif data[:4] == "$131":
      self.__maxTravel[1] = float(data[5:])
    elif data[:4] == "$132":
      self.__maxTravel[2] = float(data[5:])
    elif data[:4] == "$133":
      self.__maxTravel[3] = float(data[5:])
    elif data[:4] == "$134":
      self.__maxTravel[4] = float(data[5:])
    elif data[:4] == "$135":
      self.__maxTravel[5] = float(data[5:])

    if not self.__grblConfigLoaded:
      retour = self.__decode.decodeGrblData(data)
      if retour is not None and retour != "":
        self.logGrbl.append(retour)
      else:
        self.logGrbl.append(data)


  @pyqtSlot(str)
  def on_sig_emit(self, data: str):
    trouve = False
    if data != "":
      self.logGrbl.append(data)
      if self.__cycleRun:
        # Recherche la ligne dans la liste du fichier GCode
        ligne = self.__gcodeFile.getGCodeSelectedLine()[0]
        while ligne < self.ui.gcodeTable.model().rowCount():
          idx = self.ui.gcodeTable.model().index(ligne, 0, QModelIndex())
          if self.ui.gcodeTable.model().data(idx) == data:
            self.__gcodeFile.selectGCodeFileLine(ligne)
            trouve = True
            break
          else:
            ligne += 1
        # Mise à jour de la progressBox
        if trouve:
          self.__pBox.setValue(ligne + 1)
        # On affiche le dernier commentaire rencontré dans la progressBox
        if data[:1] == '(' and data[-1:] == ")":
          self.__pBox.setComment(data)

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
  def on_mnuResetSerial(self):
    ''' Force l'envoi de \n pour déblocage communication
    '''
    self.__grblCom.resetSerial()


  @pyqtSlot(int)
  def on_mnuHelpProbe(self, helpPage: int):
    dlgHelp = cn5XHelpProbe(helpPage)
    dlgHelp.setParent(self)
    dlgHelp.showDialog()


  @pyqtSlot()
  def on_mnuA_propos(self):
    ''' Appel de la boite de dialogue A Propos
    '''
    dlgApropos = cn5XAPropos(self.tr("Version {}.{}").format(APP_VERSION_STRING, APP_VERSION_DATE), self.__licenceFile)
    dlgApropos.setParent(self)
    dlgApropos.showDialog()


  @pyqtSlot()
  def on_btnDebug(self):
    ''' Set the debug menu on the same status '''
    if self.ui.btnDebug.isChecked():
      if not self.ui.mnuDebug_mode.isChecked():
        self.ui.mnuDebug_mode.setChecked(True)
      self.ui.btnPausePooling.setEnabled(True)
      self.on_sig_debug("cn5X++ (v{}.{}) : Starting debug.".format(APP_VERSION_STRING, APP_VERSION_DATE))
    else:
      self.on_sig_debug("cn5X++ (v{}.{}) : Stop debugging.".format(APP_VERSION_STRING, APP_VERSION_DATE))
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


  def startCycle(self, startFrom: int = 0):

    if self.ui.gcodeTable.model().rowCount()<=0:
      self.log(logSeverity.warning.value, self.tr("Attempt to start an empty cycle..."))
    else:
      self.log(logSeverity.info.value, self.tr("Starting cycle..."))

      # Affichage de la boite de progression
      self.__pBox.setRange(startFrom, self.ui.gcodeTable.model().rowCount())
      self.__pBox.start()

      self.__gcodeFile.selectGCodeFileLine(0)
      self.__cycleRun = True
      self.__cyclePause = False

      self.__gcodeFile.enQueue(self.__grblCom, startFrom)

      # Attente de la fin du traitement par Grbl
      tDebut = time.time()
      while (time.time() - tDebut) * 1000 < 2 * GRBL_QUERY_DELAY:
        QCoreApplication.processEvents()
      while self.__decode.get_etatMachine() != GRBL_STATUS_IDLE:
        QCoreApplication.processEvents()

      self.log(logSeverity.info.value, self.tr("Cycle completed."))

      self.__pBox.setComment(self.tr("GCode finished at: {}").format(datetime.now().strftime("%A %x %H:%M:%S")))

      self.ui.btnStart.setButtonStatus(False)
      self.ui.btnPause.setButtonStatus(False)
      self.ui.btnStop.setButtonStatus(True)

      if self.__pBox.isVisible():
        if self.__pBox.autoClose():
          self.__pBox.stop()
        else:
          self.__pBox.enableClose()


  def pauseCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      self.log(logSeverity.warning.value, self.tr("Holding in progress, can't restart now."))
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      self.log(logSeverity.info.value, self.tr("Resuming cycle..."))
      self.__grblCom.realTimePush(REAL_TIME_CYCLE_START_RESUME)
      self.__cyclePause = False
      self.ui.btnStart.setButtonStatus(True)
      self.ui.btnPause.setButtonStatus(False)
      self.ui.btnStop.setButtonStatus(False)
    else:
      self.log(logSeverity.info.value, self.tr("Holding cycle..."))
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      self.__cyclePause = True
      self.ui.btnStart.setButtonStatus(False)
      self.ui.btnPause.setButtonStatus(True)
      self.ui.btnStop.setButtonStatus(False)


  def stopCycle(self):
    if self.ui.lblEtat.text() == GRBL_STATUS_HOLD0:
      # Deja en pause, on vide la file d'attente et on envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Stopping cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    elif self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
      # Attente que le Hold soit termine
      self.log(logSeverity.info.value, self.tr("Holding cycle before stopping..."))
      while self.ui.lblEtat.text() == GRBL_STATUS_HOLD1:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Stopping cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    else:
      # Envoie une pause
      self.log(logSeverity.info.value, self.tr("Holding cycle before stopping..."))
      self.__grblCom.realTimePush(REAL_TIME_FEED_HOLD)
      # Attente que le Hold soit termine
      while self.ui.lblEtat.text() != GRBL_STATUS_HOLD0:
        QCoreApplication.processEvents()
      # Puis, vide la file d'attente et envoie un SoftReset
      self.log(logSeverity.info.value, self.tr("Stopping cycle..."))
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(REAL_TIME_SOFT_RESET) # Envoi Ctrl+X.
    self.__cycleRun = False
    self.__cyclePause = False
    # Masque de la boite de progression
    if self.__pBox.isVisible():
      if self.__pBox.autoClose():
        self.__pBox.stop()
      else:
        self.__pBox.enableClose()
    self.ui.btnStart.setButtonStatus(False)
    self.ui.btnPause.setButtonStatus(False)
    self.ui.btnStop.setButtonStatus(True)
    self.log(logSeverity.info.value, self.tr("Cycle stopped."))


  def on_gcodeTableContextMenu(self, event):
    if self.__gcodeFile.isFileLoaded():
      self.cMenu = QtWidgets.QMenu(self)
      editAction = QtWidgets.QAction(self.tr("Edit line"), self)
      editAction.triggered.connect(lambda: self.editGCodeSlot(event))
      self.cMenu.addAction(editAction)
      insertAction = QtWidgets.QAction(self.tr("Insert line"), self)
      insertAction.triggered.connect(lambda: self.insertGCodeSlot(event))
      self.cMenu.addAction(insertAction)
      ajoutAction = QtWidgets.QAction(self.tr("Add line"), self)
      ajoutAction.triggered.connect(lambda: self.ajoutGCodeSlot(event))
      self.cMenu.addAction(ajoutAction)
      supprimeAction = QtWidgets.QAction(self.tr("Suppress line"), self)
      supprimeAction.triggered.connect(lambda: self.supprimeGCodeSlot(event))
      self.cMenu.addAction(supprimeAction)
      self.cMenu.addSeparator()
      runAction = QtWidgets.QAction(self.tr("Run this line\t(F7)"), self)
      runAction.setShortcut('F7')
      runAction.triggered.connect(lambda: self.runGCodeSlot(event))
      self.cMenu.addAction(runAction)
      startFromHereAction = QtWidgets.QAction(self.tr("Run from this line\t(F8)"), self)
      startFromHereAction.setShortcut('F8')
      startFromHereAction.triggered.connect(lambda: self.startFromGCodeSlotIndex(event))
      self.cMenu.addAction(startFromHereAction)
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


  def runGCodeSlot(self, event = None):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.__gcodeFile.enQueue(self.__grblCom, idx[0].row(), idx[0].row())
    self.__gcodeFile.selectGCodeFileLine(idx[0].row()+1)


  def startFromGCodeSlotIndex(self, event = None):
    idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
    self.startCycle(idx[0].row())


  @pyqtSlot() #QtGui.QKeyEvent)
  def on_GCodeTable_key_F7_Pressed(self):
    if self.ui.gcodeTable.hasFocus() and self.__gcodeFile.isFileLoaded():
      idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
      self.runGCodeSlot()


  @pyqtSlot()
  def on_GCodeTable_key_F8_Pressed(self):
    if self.ui.gcodeTable.hasFocus() and self.__gcodeFile.isFileLoaded():
      idx = self.ui.gcodeTable.selectionModel().selectedIndexes()
      self.startFromGCodeSlotIndex()


  def on_dialAvanceContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    resetAction = QtWidgets.QAction(self.tr("Reset feedrate to 100%"), self)
    resetAction.triggered.connect(lambda: self.ui.dialAvance.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_dialBrocheContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    resetAction = QtWidgets.QAction(self.tr("Reset spindle speed to 100%"), self)
    resetAction.triggered.connect(lambda: self.ui.dialBroche.setValue(100))
    self.cMenu.addAction(resetAction)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblPosContextMenu(self, axis: str):
    self.cMenu = QtWidgets.QMenu(self)
    resetX = QtWidgets.QAction(self.tr("Place the {} origin of axis {} here").format(self.__decode.getG5actif(), self.__axisNames[axis]), self)
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush("G10P0L20{}0".format(self.__axisNames[axis])))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction(self.tr("Place the {} origin of all axis here").format(self.__decode.getG5actif()), self)
    axesTraites = []
    gcodeString = "G10P0L20"
    for a in self.__axisNames:
      if a not in axesTraites:
        gcodeString += "{}0 ".format(a)
        axesTraites.append(a)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush(gcodeString))
    self.cMenu.addAction(resetAll)
    self.cMenu.addSeparator()
    resetX = QtWidgets.QAction(self.tr("Jog axis {} to {} origin").format(self.__axisNames[axis], self.__decode.getG5actif()), self)
    cmdJog1 = CMD_GRBL_JOG + "G90G21F{}{}0".format(self.ui.dsbJogSpeed.value(), self.__axisNames[axis])
    resetX.triggered.connect(lambda: self.__grblCom.gcodePush(cmdJog1))
    self.cMenu.addAction(resetX)
    resetAll = QtWidgets.QAction(self.tr("Jog all axis to {} origin").format(self.__decode.getG5actif()), self)
    axesTraites = []
    cmdJog = CMD_GRBL_JOG + "G90G21F{}".format(self.ui.dsbJogSpeed.value())
    for a in self.__axisNames:
      if a not in axesTraites:
        cmdJog += "{}0 ".format(a)
        axesTraites.append(a)
    resetAll.triggered.connect(lambda: self.__grblCom.gcodePush(cmdJog))
    self.cMenu.addAction(resetAll)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblGXXContextMenu(self, piece: int):
    self.cMenu = QtWidgets.QMenu(self)
    setOrigineAll = QtWidgets.QAction(self.tr("Place the workpiece origin {} (G{})").format(str(piece), str(piece + 53)), self)

  def on_lblPlanContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    planXY = QtWidgets.QAction(self.tr("G17 Working plane - XY (Defaut)"), self)
    planXY.triggered.connect(lambda: self.__grblCom.gcodePush("G17"))
    self.cMenu.addAction(planXY)
    planXZ = QtWidgets.QAction(self.tr("G18 Working plane - XZ"), self)
    planXZ.triggered.connect(lambda: self.__grblCom.gcodePush("G18"))
    self.cMenu.addAction(planXZ)
    planYZ = QtWidgets.QAction(self.tr("G19 Working plane - YZ"), self)
    planYZ.triggered.connect(lambda: self.__grblCom.gcodePush("G19"))
    self.cMenu.addAction(planYZ)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblUnitesContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction(self.tr("G20 - Work units in inches"), self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G20"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction(self.tr("G21 - Work units in millimeters"), self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G21"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


  def on_lblCoordContextMenu(self):
    self.cMenu = QtWidgets.QMenu(self)
    unitePouces = QtWidgets.QAction(self.tr("G90 - Absolute coordinates movements"), self)
    unitePouces.triggered.connect(lambda: self.__grblCom.gcodePush("G90"))
    self.cMenu.addAction(unitePouces)
    uniteMM = QtWidgets.QAction(self.tr("G91 - relative coordinates movements"), self)
    uniteMM.triggered.connect(lambda: self.__grblCom.gcodePush("G91"))
    self.cMenu.addAction(uniteMM)
    self.cMenu.popup(QtGui.QCursor.pos())


  def createLangMenu(self):
    ''' Creation du menu de choix de la langue du programme
    en fonction du contenu du fichier i18n/cn5X_locales.xml '''
    fichierXML = QFile(":/i18n/i18n/cn5X_locales.xml")
    if fichierXML.open(QFile.ReadOnly):
      XMLbuff = str(fichierXML.readAll(), 'utf-8')
    else:
      print("Error reading cn5X_locales.xml from resources !")

    document = parseString(XMLbuff)
    root = document.documentElement
    translations = root.getElementsByTagName("translation")

    l = 0
    self.langues = []
    self.ui.actionLang = []
    self.ui.iconLang = []
    for translation in translations:

      self.langues.append(translation.getElementsByTagName("locale")[0].childNodes[0].nodeValue)
      label = translation.getElementsByTagName("label")[0].childNodes[0].nodeValue
      qm_file = translation.getElementsByTagName("qm_file")[0].childNodes[0].nodeValue
      flag_file = translation.getElementsByTagName("flag_file")[0].childNodes[0].nodeValue

      self.ui.actionLang.append(QtWidgets.QAction(self))
      self.ui.iconLang.append(QtGui.QIcon())
      self.ui.iconLang[l].addPixmap(QtGui.QPixmap(flag_file), QtGui.QIcon.Normal, QtGui.QIcon.Off)
      self.ui.actionLang[l].setIcon(self.ui.iconLang[l])
      self.ui.actionLang[l].setText(label)
      self.ui.actionLang[l].setCheckable(True)
      font = QtGui.QFont()
      font.setPointSize(12)
      self.ui.actionLang[l].setFont(font)
      self.ui.actionLang[l].setObjectName(self.langues[l])
      self.ui.menuLangue.addAction(self.ui.actionLang[l])

      l += 1

    self.ui.menuLangue.addSeparator()
    self.actionLangSystem = QtWidgets.QAction()
    self.actionLangSystem.setCheckable(True)
    font = QtGui.QFont()
    font.setPointSize(12)
    self.actionLangSystem.setFont(font)
    self.actionLangSystem.setObjectName("actionLangSystem")
    self.ui.menuLangue.addAction(self.actionLangSystem)
    self.actionLangSystem.setText(self.tr("Use system language"))

    self.ui.menuLangue.triggered.connect(self.on_menuLangue)


  def on_menuLangue(self, action):
    if action.objectName() == "actionLangSystem":
      langue = QLocale()
      self.__settings.remove("lang")
    else:
      langue = QLocale(action.objectName())
      self.__settings.setValue("lang", action.objectName())
    # Active la nouvelle langue
    self.setTranslator(langue)
    #for a in self.ui.menuLangue.actions():
    #  if a.objectName() == action.objectName():
    #    a.setChecked(True)
    #  else:
    #    a.setChecked(False)


  @pyqtSlot(bool)
  def on_sig_activity(self, val: bool):
    if val:
      # Serial send/receive in progress
      self.ui.lblSerialActivity.setStyleSheet(".QLabel{border-radius: 3px; background: red;}")
    else:
      # Serial send/receive done
      self.ui.lblSerialActivity.setStyleSheet(".QLabel{border-radius: 3px; background: green;}")


  @pyqtSlot(bool)
  def on_sig_serialLock(self, val: bool):
    if val:
      # OK to send GCode = True
      self.ui.lblSerialLock.setStyleSheet(".QLabel{border-radius: 3px; background: green;}")
    else:
      # OK to send GCode = False
      self.ui.lblSerialLock.setStyleSheet(".QLabel{border-radius: 3px; background: red;}")


  def setTranslator(self, langue: QLocale):
    ''' Active la langue de l'interface '''
    global translator # Reutilise le translateur de l'objet app
    ###if not translator.load(langue, "{}/i18n/cn5X".format(app_path), "."):
    if not translator.load(langue, ":/i18n/i18n/cn5X", "."):
      self.log(logSeverity.error.value, self.tr("Locale ({}) not usable, using default to english").format(langue.name()))
      #langue = QLocale(QLocale.French, QLocale.France)
      langue = QLocale(QLocale.English, QLocale.UnitedKingdom)
      ###translator.load(langue, "{}/i18n/cn5X".format(app_path), ".")
      translator.load(langue, ":/i18n/i18n/cn5X", ".")

    # Install le traducteur et l'exécute sur les éléments déjà chargés
    QtCore.QCoreApplication.installTranslator(translator)
    self.ui.retranslateUi(self)
    self.actionLangSystem.setText(self.tr("Use system language"))

    # Coche le bon item dans le menu langue
    settingsLang = self.__settings.value("lang", "default")
    for a in self.ui.menuLangue.actions():
      if a.objectName() == "actionLangSystem":
        if settingsLang == "default":
          a.setChecked(True)
        else:
          a.setChecked(False)
      else:
        la = QLocale(a.objectName())
        if la.language() == langue.language():
          self.ui.menuLangue.setIcon(a.icon())
          if settingsLang != "default":
            a.setChecked(True)
          else:
            a.setChecked(False)
        else:
          a.setChecked(False)

    # Sélectionne l'image du bouton d'urgence
    if langue.language() == QLocale(QLocale.French, QLocale.France).language():
      self.btnUrgencePictureLocale = ":/cn5X/images/btnUrgence.svg"
      self.btnUrgenceOffPictureLocale = ":/cn5X/images/btnUrgenceOff.svg"
    else:
      self.btnUrgencePictureLocale = ":/cn5X/images/btnEmergency.svg"
      self.btnUrgenceOffPictureLocale = ":/cn5X/images/btnEmergencyOff.svg"
    # et relance l'affichage avec la nouvelle image
    self.setEnableDisableGroupes()


"""******************************************************************"""


if __name__ == '__main__':
  
  # Suppress qt.qpa.xcb: QXcbConnection: XCB error: 3 (BadWindow)
  os.environ["QT_LOGGING_RULES"] = '*.debug=false;qt.qpa.*=false'
  
  app = QtWidgets.QApplication(sys.argv)

  # Retrouve le répertoire de l'exécutable
  if getattr(sys, 'frozen', False):
    # frozen
    app_path = os.path.dirname(sys.executable)
  else:
    # unfrozen
    app_path = os.path.dirname(os.path.realpath(__file__))

  # Bannière sur la console...
  print("{} v{}.{} running from: {}".format(APP_NAME, APP_VERSION_STRING, APP_VERSION_DATE, app_path))
  print("")
  print("                ####### #     #")
  print("  ####   #    # #        #   #     #       #")
  print(" #    #  ##   # #         # #      #       #")
  print(" #       # #  #  #####     #     #####   #####")
  print(" #       #  # #       #   # #      #       #")
  print(" #    #  #   ## #     #  #   #     #       #")
  print("  ####   #    #  #####  #     #")
  print("")

  # Chargement police LED Calculator depuis le fichier de ressources
  QFontDatabase.addApplicationFont(":/cn5X/fonts/LEDCalculator.ttf")
  QFontDatabase.addApplicationFont(":/cn5X/fonts/DSEG14Classic.ttf")
  QFontDatabase.addApplicationFont(":/cn5X/fonts/DSEG14ClassicMini.ttf")

  translator = QTranslator()
  langue = QLocale(QLocale.French, QLocale.France)
  translator.load(langue, ":/i18n/i18n/cn5X", ".")
  app.installTranslator(translator)
  
  # Définition de la locale pour affichage des dates dans la langue du systeme
  try:
    locale.setlocale(locale.LC_TIME, '')
  except Exception as err:
    print("Warning: {}".format(err))

  window = winMain()

  # Traque tous les évennements de l'appli pour gestion de la veille en
  # mode plein écran
  appEvents = appEventFilter(win=window)
  app.installEventFilter(appEvents)
  derniereActivite = time.time()
  
  window.show()
  sys.exit(app.exec_())
