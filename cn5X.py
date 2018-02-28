# !/usr/bin/env python
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

import sys, os, time #, datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, pyqtSlot, QModelIndex,  QItemSelectionModel
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt5.QtSerialPort import QSerialPortInfo
import mainWindow
from cn5X_config import *
from msgbox import *
####from grblCommunicator import grblCommunicator
from grblCom import grblCom
from grblDecode import grblDecode
from gcodeQLineEdit import gcodeQLineEdit
from cnQPushButton import cnQPushButton
from grblJog import grblJog

defaultBaudRate = 115200

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)
    self.ui = mainWindow.Ui_mainWindow()

    self.ui.setupUi(self)
    self.logGrbl  = self.ui.txtGrblOutput    # Tous les messages de Grbl seront redirigés dans le widget txtGrblOutput
    self.logCn5X  = self.ui.txtConsoleOutput # Tous les messages applicatif seront redirigés dans le widget txtConsoleOutput
    self.logDebug = self.ui.txtDebugOutput   # Message debug de Grbl

    self.logGrbl.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes
    self.logCn5X.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes
    self.logDebug.document().setMaximumBlockCount(2000) # Limite la taille des logs à 2000 lignes

    self.gcodeFileContent = QStandardItemModel(self.ui.listGCodeFile)

    self.timerDblClic = QtCore.QTimer()
    self.decode = grblDecode(self.ui)

    ####self.__grblCom = grblCommunicator()
    ####self.__grblCom.sig_msg.connect(self.on_communicator_msg)           # Messages de fonctionnements du communicator
    ####self.__grblCom.sig_init.connect(self.on_communicator_init)         # Grbl initialisé
    ####self.__grblCom.sig_grblOk.connect(self.on_ok)                      # Reponse : ok
    ####self.__grblCom.sig_grblResponse.connect(self.on_communicator_rep)  # Reponse : error:X ou ALARM:X
    ####self.__grblCom.sig_grblStatus.connect(self.on_communicator_status) # Ligne de status entre < et >
    ####self.__grblCom.sig_data_recived.connect(self.on_communicator_data) # Autres données de Grbl
    ####self.__grblCom.sig_data_debug.connect(self.on_communicator_debug)  # Tous les messages de Grbl
    self.__grblCom = grblCom()
    self.__grblCom.sig_log.connect(self.on_sig_log)
    self.__grblCom.sig_init.connect(self.on_sig_init)
    self.__grblCom.sig_ok.connect(self.on_sig_ok)
    self.__grblCom.sig_error.connect(self.on_sig_error)
    self.__grblCom.sig_alarm.connect(self.on_sig_alarm)
    self.__grblCom.sig_status.connect(self.on_sig_status)
    self.__grblCom.sig_data.connect(self.on_sig_data)
    self.__grblCom.sig_emit.connect(self.on_sig_emit)
    self.__grblCom.sig_recu.connect(self.on_sig_recu)
    self.__grblCom.sig_debug.connect(self.on_sig_debug)

    self.__jog = grblJog(self.__grblCom)

    self.__connectionStatus = False
    self.__arretUrgence = True

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
      if v == defaultBaudRate:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenêtre (status bar)
    self.ui.statusBar.showMessage("")

    # Positionne l'état d'activation des contrôles
    self.setEnableDisableGroupes()

    """---------- Connections des évennements de l'interface graphique ----------"""
    self.ui.btnUrgence.pressed.connect(self.on_arretUrgence)             # Evenements du bouton d'arrêt d'urgence
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed) # un clic sur un élément de la liste appellera la méthode 'on_cmbPort_changed'
    self.ui.mnuAppOuvrir.triggered.connect(self.on_mnuAppOuvrir)         # Connexions des routines du menu application
    self.ui.mnuAppQuitter.triggered.connect(self.on_mnuAppQuitter)
    self.ui.mnu_MPos.triggered.connect(self.on_mnu_MPos)
    self.ui.mnu_WPos.triggered.connect(self.on_mnu_WPos)
    self.ui.btnRefresh.clicked.connect(self.populatePortList)            # Refresh de la liste des ports serie
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)           # un clic sur le bouton "(De)Connecter" appellera la méthode 'action_btnConnect'
    self.ui.btnSend.pressed.connect(self.sendCmd)                        # Bouton d'envoi de commandes unitaires
    self.ui.txtGCode.returnPressed.connect(self.sendCmd)                 # Même fonction par la touche entrée
    self.ui.txtGCode.textChanged.connect(self.txtGCode_on_Change)        # Analyse du champ de saisie au fur et a mesure de son édition
    self.ui.txtGCode.keyPressed.connect(self.on_keyPressed)
    self.ui.btnStartTimer.clicked.connect(self.startTimer)
    self.ui.btnStopTimer.clicked.connect(self.stopTimer)
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
    self.ui.btnJogStop.mousePress.connect(self.on_jogCancel)

  def populatePortList(self):
    ''' Rempli la liste des ports série '''
    self.ui.cmbPort.clear()
    self.ui.cmbPort.addItem("")
    if len(QSerialPortInfo.availablePorts()) > 0:
      for p in QSerialPortInfo.availablePorts():
        self.ui.cmbPort.addItem(p.portName() + ' - ' + p.description())
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
    # S'il n'y a qu'un seul port série, on le sélectionne
    if len(QSerialPortInfo.availablePorts()) == 1:
      self.ui.cmbPort.setCurrentIndex(1)

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
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(False)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      self.ui.frmCoordOffsets.setEnabled(False)
    elif self.__arretUrgence:
      # Connecté mais sous arrêt d'urgence : Tout est désactivé sauf l'arrêt d'urgence
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
      self.ui.frmCoordOffsets.setEnabled(False)
    else:
      # Tout est en ordre, on active tout
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgence.svg'))
      self.ui.btnUrgence.setToolTip("Arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(True)
      self.ui.grpJog.setEnabled(True)
      self.ui.frmGcodeInput.setEnabled(True)
      self.ui.frmBoutons.setEnabled(True)
      self.ui.frmCoordOffsets.setEnabled(True)

  @pyqtSlot()
  def on_mnuAppOuvrir(self):
    # Affiche la boite de dialogue
    opt = QtWidgets.QFileDialog.Options()
    opt |= QtWidgets.QFileDialog.DontUseNativeDialog
    fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Ouvrir un fichier GCode", "", "Fichier GCode (*.gcode *.ngc *.nc *.gc *.cnc)", options=opt)
    if fileName[0] != "":
      # Lecture du fichier
      self.logCn5X.append("Lecture du fichier : " + fileName[0])
      try:
        f = open(fileName[0],'r')
        lignes  = f.readlines()
        f.close()
        # Envoi du contenu dans la liste
        self.gcodeFileContent.clear()
        for l in lignes:
          #print("["+l.strip()+"]")
          item = QStandardItem(l.strip())
          #item.setCheckable(True)
          self.gcodeFileContent.appendRow(item)
        self.ui.listGCodeFile.setModel(self.gcodeFileContent)
        # Sélectionne la premiere ligne du fichier dans la liste
        self.selectGCodeFileLine(0)
        # Sélectionne l'onglet du fichier
        self.ui.grpConsole.setCurrentIndex(1)
      except Exception as e:
        self.logCn5X.append("Erreur lecture du fichier : " + fileName[0])
        self.logCn5X.append(str(e))
        # Sélectionne l'onglet de la console pour que le message s'affiche
        self.ui.grpConsole.setCurrentIndex(2)

  def selectGCodeFileLine(self, num: int):
    # Selectionne un élément de la liste du fichier GCode
    idx = self.gcodeFileContent.index(num, 0, QModelIndex())
    self.ui.listGCodeFile.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectCurrent)

  def getGCodeSelectedLine(self):
    indexes = self.ui.listGCodeFile.selectionModel().selectedIndexes()
    return self.gcodeFileContent.data(indexes[0])

  @pyqtSlot()
  def on_mnuAppQuitter(self):
    if self.__connectionStatus:
      self.__grblCom.stopCommunicator()
    self.ui.statusBar.showMessage("Bye-bye...")
    self.close()

  def closeEvent(self, event):
    if self.__connectionStatus:
      ####self.__grblCom.stopCommunicator()
      self.__grblCom.stopCom()
    self.ui.statusBar.showMessage("Bye-bye...")
    event.accept() # let the window close

  def on_mnu_MPos(self, check):
    if check:
      param10 = 255 # Le bit 1 est à 1
      ####self.__grblCom.addLiFo("$10=" + str(param10))
      self.__grblCom.gcodeInsert("$10=" + str(param10))


  def on_mnu_WPos(self, check):
    if check:
      param10 = 255 ^ 1 # Met le bit 1 à 0
      ####self.__grblCom.addLiFo("$10=" + str(param10))
      self.__grblCom.gcodeInsert("$10=" + str(param10))


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
    else:
      self.__grblCom.clearCom() # Vide la file d'attente de communication
      self.__grblCom.realTimePush(chr(0x18)) # Envoi Ctrl+X.
      self.__arretUrgence = True
      print("Arrêt d'urgence STOP !!!")

    # Actualise l'état actif/inactif des groupes de contrôles de pilotage de Grbl
    self.setEnableDisableGroupes()

  @pyqtSlot()
  def action_btnConnect(self):
    if self.ui.btnConnect.text() == "Connecter":
      # Recupère les coordonnées et paramètres du port à connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      baudRate = int(self.ui.cmbBauds.currentText())
      # Démarrage du communicator
      ####self.__grblCom.startCommunicator(serialDevice, baudRate)
      self.__grblCom.startCom(serialDevice, baudRate)
      # Mise à jour de l'interface
      self.ui.lblConnectStatus.setText("Connecté à " + serialDevice)
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
      self.setEnableDisableConnectControls()
      self.__connectionStatus = True
      # Active les groupes de contrôles de pilotage de Grbl
      self.setEnableDisableGroupes()

    else:
      # Arret du comunicator
      ####self.__grblCom.stopCommunicator()
      self.__grblCom.stopCom()
      self.__connectionStatus = False
      # Mise à jour de l'interface
      self.ui.lblConnectStatus.setText("<Non Connecté>")
      self.ui.btnConnect.setText("Connecter") # La prochaine action du bouton sera pour connecter
      self.ui.statusBar.showMessage("")
      self.setEnableDisableConnectControls()
      # Force la position de l'arrêt d'urgence
      self.__arretUrgence = True
      # Active les groupes de contrôles de pilotage de Grbl
      self.setEnableDisableGroupes()

  @pyqtSlot()
  def on_cmbPort_changed(self):
    self.setEnableDisableConnectControls()

  @pyqtSlot()
  def on_btnSpinM3(self):
    self.logGrbl.append("M3")
    ####self.__grblCom.addLiFo("M3")
    self.__grblCom.gcodeInsert("M3")
    self.ui.btnSpinM4.setEnabled(False) # Interdit un changement de sens de rotation direct

  @pyqtSlot()
  def on_btnSpinM4(self):
    self.logGrbl.append("M4")
    ####self.__grblCom.addLiFo("M4")
    self.__grblCom.gcodeInsert("M4")
    self.ui.btnSpinM3.setEnabled(False) # Interdit un changement de sens de rotation direct

  @pyqtSlot()
  def on_btnSpinM5(self):
    self.logGrbl.append("M5")
    ####self.__grblCom.addLiFo("M5")
    self.__grblCom.gcodeInsert("M5")
    self.ui.btnSpinM3.setEnabled(True)
    self.ui.btnSpinM4.setEnabled(True)

  @pyqtSlot()
  def on_btnFloodM7(self):
    if self.decode.get_etatArrosage() != "M7" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M7")
      ####self.__grblCom.sendData(chr(0xA1))
      self.__grblCom.realTimePush(chr(0xA1))

  @pyqtSlot()
  def on_btnFloodM8(self):
    if self.decode.get_etatArrosage() != "M8" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M8")
      ####self.__grblCom.sendData(chr(0xA0))
      self.__grblCom.realTimePush(chr(0xA0))

  @pyqtSlot()
  def on_btnFloodM9(self):
    if self.decode.get_etatArrosage() == "M7" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      ####self.__grblCom.sendData(chr(0xA1))
      self.__grblCom.realTimePush(chr(0xA1))
    if self.decode.get_etatArrosage() == "M8" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M9")
      ####self.__grblCom.sendData(chr(0xA0))
      self.__grblCom.realTimePush(chr(0xA0))

  @pyqtSlot(str, QtGui.QMouseEvent)
  def on_lblG5xClick(self, lblText, e):
    self.logGrbl.append(lblText)
    ####self.__grblCom.addLiFo(lblText)
    self.__grblCom.gcodeInsert(lblText)

  @pyqtSlot()
  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      self.logGrbl.append(self.ui.txtGCode.text().upper())
      if self.ui.txtGCode.text() == "?":
        self.decode.getNextStatus()
    self.__grblCom.gcodePush(self.ui.txtGCode.text())
    self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
    self.ui.txtGCode.setFocus()

  @pyqtSlot()
  def txtGCode_on_Change(self):
    if self.ui.txtGCode.text() == "?":
      self.logGrbl.append("?")
      self.decode.getNextStatus()
      ####self.__grblCom.sendData("?") # Envoi direct si ? sans attendre le retour chariot.
      self.__grblCom.realTimePush("?") # Envoi direct si ? sans attendre le retour chariot.
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))

  @pyqtSlot(QtGui.QKeyEvent)
  def on_keyPressed(self, e):
    if QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+C"):
      print("Ctrl+C")
    elif QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+X"):
      self.logGrbl.append("Ctrl+X")
      ####self.__grblCom.sendData(chr(0x18)) # Envoi direct Ctrl+X.
      self.__grblCom.realTimePush(chr(0x18)) # Envoi direct Ctrl+X.


  @pyqtSlot(cnQPushButton, QtGui.QMouseEvent)
  def on_jog(self, cnButton, e):
    print("on_jog({}), mouseDown = {}".format(cnButton.name(), cnButton.isMouseDown()))
    if cnButton.name() == "btnJogPlusX":
      if self.ui.rbtJog0000.isChecked:
        # On envoie des petits mouvements tant que le bouton est enfoncé
        while cnButton.isMouseDown():
          time.sleep(50 / 1000)
          self.__jog.jogX(0.0125) # 1 pas à 80 pas par mm
          self.logGrbl.append("jogX(0.05)")
          QCoreApplication.processEvents()
          time.sleep(50 / 1000)
        print("MouseUp")
        self.__jog.jogCancel()
    elif cnButton.name() == "btnJogMoinsX":
      if self.ui.rbtJog0000.isChecked:
        # On envoie des petits mouvements tant que le bouton est enfoncé
        while cnButton.isMouseDown():
          time.sleep(50 / 1000)
          self.__jog.jogX(-0.0125)
          self.logGrbl.append("jogX(0.05)")
          QCoreApplication.processEvents()
          time.sleep(50 / 1000)
        print("MouseUp")
        self.__jog.jogCancel()

  def on_jogCancel(self):
    ####self.__grblCom.sendData(chr(0x85)) # Envoi direct Jog Cancel
    self.__grblCom.clearCom()
    self.__grblCom.realTimePush(chr(0x85)) # Envoi direct Jog Cancel

  @pyqtSlot(int, str)
  def on_sig_log(self, severity: int, data: str):
    ####def on_communicator_msg(self, data: str):
    self.logCn5X.append("[{}] ".format(severity) + data)

  @pyqtSlot(str)
  def on_sig_init(self, data: str):
    ####def on_communicator_init(self, data: str):
    self.logGrbl.append(data)
    self.ui.statusBar.showMessage(data.split("[")[0])

  @pyqtSlot()
  def on_sig_ok(self):
    ####def on_ok(self):
    self.logGrbl.append("ok")

  @pyqtSlot(int)
  def on_sig_error(self, errNum: int):
    self.logGrbl.append(self.decode.errorMessage(errNum))

  @pyqtSlot(int)
  def on_sig_alarm(self, alarmNum: int):
    self.logGrbl.append(self.decode.alarmMessage(alarmNum))


  '''
  @pyqtSlot(str)
  def on_communicator_rep(self, data: str):
    retour = self.decode.decodeGrblResponse(data)
    if retour != "":
      self.logGrbl.append(retour)
  '''

  @pyqtSlot(str)
  def on_sig_status(self, data: str):
    ####def on_communicator_status(self, data: str):
    retour = self.decode.decodeGrblStatus(data)
    if retour != "":
      self.logGrbl.append(retour)

  @pyqtSlot(str)
  def on_sig_data(self, data: str):
    ####def on_communicator_data(self, data: str):
    retour = self.decode.decodeGrblData(data)
    if retour is not None and retour != "":
      self.logGrbl.append(retour)

  @pyqtSlot(str)
  def on_sig_emit(self, data: str):
    pass

  @pyqtSlot(str)
  def on_sig_recu(self, data: str):
    pass

  @pyqtSlot(str)
  def on_sig_debug(self, data: str):
    ####def on_communicator_debug(self, data: str):
    if self.ui.mnuDebug_mode.isChecked():
      self.logDebug.append(data)

  @pyqtSlot()
  def stopTimer(self):
    self.__grblCom.stopTimer()

  @pyqtSlot()
  def startTimer(self):
    self.__grblCom.startTimer()

  @pyqtSlot()
  def clearDebug(self):
    self.logDebug.clear()

if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
