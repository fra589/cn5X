# !/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, os, datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtSerialPort import QSerialPortInfo
import mainWindow
from msgbox import *
from grblCommunicator import grblCommunicator
from grblDecode import grblDecode
from gcodeQLineEdit import gcodeQLineEdit

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

    self.timerDblClic = QtCore.QTimer()
    self.decode = grblDecode(self.ui)

    self.__grblCom = grblCommunicator()
    self.__grblCom.sig_msg.connect(self.on_communicator_msg)           # Messages de fonctionnements du communicator
    self.__grblCom.sig_init.connect(self.on_communicator_init)         # Grbl initialisé
    self.__grblCom.sig_grblOk.connect(self.on_ok)                      # Reponse : ok
    self.__grblCom.sig_grblResponse.connect(self.on_communicator_rep)  # Reponse : error:X ou ALARM:X
    self.__grblCom.sig_grblStatus.connect(self.on_communicator_status) # Ligne de status entre < et >
    self.__grblCom.sig_data_recived.connect(self.on_communicator_data) # Autres données de Grbl
    self.__grblCom.sig_data_debug.connect(self.on_communicator_debug)  # Tous les messages de Grbl

    self.__connectionStatus = False
    self.__arretUrgence = True

    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(pathname)

    """---------- Préparation de l'interface ----------"""
    ###QtGui.QFontDatabase.addApplicationFont(pathname + "/fonts/LEDCalculator.ttf") # Chargement de la police des labels de status machine
    QtGui.QFontDatabase.addApplicationFont(":/cn5X/fonts/LEDCalculator.ttf")
    self.ui.btnConnect.setText("Connecter")                                       # Label du bouton connect
    self.populatePortList()                                                       # On rempli la liste des ports série

    app.setStyleSheet("QToolTip { background-color: rgb(248, 255, 192); color: rgb(0, 0, 63); }")

    curIndex = -1                                                                  # On rempli la liste des vitesses
    for v in QSerialPortInfo.standardBaudRates():
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == defaultBaudRate:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenêtre (status bar)
    self.ui.statusBar.showMessage("")

    # Positionne l'état d'activation des contrôles
    self.setEnableDisableGroupes()

    """---------- Connections des évennements traités ----------"""
    self.ui.btnUrgence.pressed.connect(self.on_arretUrgence)                # Evenements du bouton d'arrêt d'urgence
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
    self.ui.btnFloodM7.clicked.connect(self.on_btnFloodM7)
    self.ui.btnFloodM8.clicked.connect(self.on_btnFloodM8)
    self.ui.btnFloodM9.clicked.connect(self.on_btnFloodM9)

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
    elif self.__arretUrgence:
      # Connecté mais sous arrêt d'urgence : Tout est désactivé sauf l'arrêt d'urgence
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(False)
      self.ui.grpJog.setEnabled(False)
      self.ui.frmGcodeInput.setEnabled(False)
      self.ui.frmBoutons.setEnabled(False)
    else:
      # Tout est en ordre, on active tout
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgence.svg'))
      self.ui.btnUrgence.setToolTip("Arrêt d'urgence")
      self.ui.frmArretUrgence.setEnabled(True)
      self.ui.frmControleVitesse.setEnabled(True)
      self.ui.grpJog.setEnabled(True)
      self.ui.frmGcodeInput.setEnabled(True)
      self.ui.frmBoutons.setEnabled(True)

  @pyqtSlot()
  def on_mnuAppOuvrir(self):
    pass

  @pyqtSlot()
  def on_mnuAppQuitter(self):
    if self.__connectionStatus:
      self.__grblCom.stopCommunicator()
    self.ui.statusBar.showMessage("Bye-bye...")
    self.close()

  def closeEvent(self, event):
    if self.__connectionStatus:
      self.__grblCom.stopCommunicator()
    self.ui.statusBar.showMessage("Bye-bye...")
    event.accept() # let the window close

  def on_mnu_MPos(self, check):
    if check:
      param10 = 255 # Le bit 1 est à 1
      self.__grblCom.sendLine("$10=" + str(param10))
    pass

  def on_mnu_WPos(self, check):
    if check:
      param10 = 255 ^ 1 # Met le bit 1 à 0
      self.__grblCom.sendLine("$10=" + str(param10))
    pass

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
      self.__grblCom.sendData(chr(0x18)) # Envoi direct Ctrl+X.
      self.__arretUrgence = True
      print("Arrêt d'urgence STOP !!!")

    # Actualise l'état actif/inactif des groupes de contrôles de pilotage de Grbl
    self.setEnableDisableGroupes()

  def action_btnConnect(self):
    if self.ui.btnConnect.text() == "Connecter":
      # Recupère les coordonnées et paramètres du port à connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      baudRate = int(self.ui.cmbBauds.currentText())
      # Démarrage du communicator
      self.__grblCom.startCommunicator(serialDevice, baudRate)
      # Mise à jour de l'interface
      self.ui.lblConnectStatus.setText("Connecté à " + serialDevice)
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
      self.setEnableDisableConnectControls()
      self.__connectionStatus = True
      # Active les groupes de contrôles de pilotage de Grbl
      self.setEnableDisableGroupes()

    else:
      # Arret du comunicator
      self.__grblCom.stopCommunicator()
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

  def on_cmbPort_changed(self):
    self.setEnableDisableConnectControls()

  def on_btnFloodM7(self):
    if self.decode.get_etatArrosage() != "M7" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M7")
      self.__grblCom.sendData(chr(0xA1))

  def on_btnFloodM8(self):
    if self.decode.get_etatArrosage() != "M8" and self.decode.get_etatArrosage() != "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M8")
      self.__grblCom.sendData(chr(0xA0))

  def on_btnFloodM9(self):
    if self.decode.get_etatArrosage() == "M7" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command"
      self.__grblCom.sendData(chr(0xA1))
    if self.decode.get_etatArrosage() == "M8" or self.decode.get_etatArrosage() == "M78":
      # Envoi "Real Time Command" plutôt que self.__grblCom.enQueue("M9")
      self.__grblCom.sendData(chr(0xA0))

  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      self.logGrbl.append(self.ui.txtGCode.text().upper())
      self.__grblCom.enQueue(self.ui.txtGCode.text())
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))
      self.ui.txtGCode.setFocus()

  def txtGCode_on_Change(self):
    if self.ui.txtGCode.text() == "?":
      self.logGrbl.append("?")
      self.__grblCom.sendData("?") # Envoi direct si ? sans attendre le retour chariot.
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))

  @pyqtSlot(QtGui.QKeyEvent)
  def on_keyPressed(self, e):
    if QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+C"):
      print("Ctrl+C")
    elif QKeySequence(e.key()+int(e.modifiers())) == QKeySequence("Ctrl+X"):
      self.logGrbl.append("Ctrl+X")
      self.__grblCom.sendData(chr(0x18)) # Envoi direct Ctrl+X.

    pass

  @pyqtSlot(str)
  def on_communicator_msg(self, data: str):
    self.logCn5X.append(data)

  @pyqtSlot(str)
  def on_communicator_init(self, data: str):
    self.logGrbl.append(data)
    self.ui.statusBar.showMessage(data.split("[")[0])

  @pyqtSlot()
  def on_ok(self):
    self.logGrbl.append("ok")
    pass

  @pyqtSlot(str)
  def on_communicator_rep(self, data: str):
    retour = self.decode.decodeGrblResponse(data)
    if retour != "":
      self.logGrbl.append(retour)

  @pyqtSlot(str)
  def on_communicator_status(self, data: str):
    retour = self.decode.decodeGrblStatus(data)
    if retour != "":
      self.logGrbl.append(retour)

  @pyqtSlot(str)
  def on_communicator_data(self, data: str):
    retour = self.decode.decodeGrblData(data)
    if retour is not None and retour != "":
      self.logGrbl.append(retour)

  @pyqtSlot(str)
  def on_communicator_debug(self, data: str):
    if self.ui.mnuDebug_mode.isChecked():
      self.logDebug.append(data)

  def stopTimer(self):
    self.__grblCom.stopTimer()

  def startTimer(self):
    self.__grblCom.startTimer()

  def clearDebug(self):
    self.logDebug.clear()

if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
