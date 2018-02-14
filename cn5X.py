#!/usr/bin/env python
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

    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    print(pathname)
    os.chdir(pathname)

    """---------- Préparation de l'interface ----------"""
    QtGui.QFontDatabase.addApplicationFont(pathname + "/fonts/LEDCalculator.ttf") # Chargement de la police des labels de status machine
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

    """---------- Connections des évennements traités ----------"""
    self.ui.btnUrgence.pressed.connect(self.arretUrgence)                # Evenements du bouton d'arrêt d'urgence
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

    self.setConnectControlsStatus()

  def setConnectControlsStatus(self):
    '''
    Active ou désactive les contrôles de connexion en fonction de l'état de sélection du port
    '''
    if self.ui.cmbPort.currentText() == "":
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setEnabled(False)
    else:
      self.ui.cmbBauds.setEnabled(True)
      self.ui.btnConnect.setEnabled(True)

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
    print("Le menu est : ", check)
    pass

  def on_mnu_WPos(self, check):
    print("Le menu est : ", check)
    pass

  def arretUrgence(self):
    print("Arrêt d'urgence détecté !")
    if not(self.ui.btnUrgence.isChecked()):
      print("STOP !!!")
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
      self.ui.btnStart.setEnabled(False)
      self.ui.btnStop.setEnabled(False)
      self.ui.btnUrgence.setToolTip("Double clic pour\ndévérouiller l'arrêt d'urgence")
    else:
      if not self.timerDblClic.isActive():
        # On est pas dans le timer du double click,
        # c'est donc un simple click qui ne suffit pas à déverrouiller le bouton d'arrêt d'urgence.
        self.timerDblClic.setSingleShot(True)
        self.timerDblClic.start(QtWidgets.QApplication.instance().doubleClickInterval())
        self.ui.btnUrgence.setChecked(False)
      else:
        print("Double click détecté,")
        print(self.timerDblClic.remainingTime()) # Double clic détecté
        self.timerDblClic.stop()
        print("On relance :-)")
        self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgence.svg'))
        self.ui.btnStart.setEnabled(True)
        self.ui.btnStop.setEnabled(True)
        self.ui.btnUrgence.setToolTip("Arrêt d'urgence")

  def action_btnConnect(self):
    if self.ui.btnConnect.text() == "Connecter":
      print('Appui bouton Connecter.')
      # Recupère les coordonnées et paramètres du port à connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      baudRate = int(self.ui.cmbBauds.currentText())
      print("Démarrage du communicator")
      self.__grblCom.startCommunicator(serialDevice, baudRate)
      self.__connectionStatus = True

      self.ui.lblConnectStatus.setText("Connecté à " + serialDevice)
      self.ui.cmbPort.setEnabled(False)
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
    else:
      print('Appui bouton Déconnecter.')
      self.__grblCom.stopCommunicator()
      self.__connectionStatus = False

      self.ui.statusBar.showMessage("")
      self.ui.lblConnectStatus.setText("<Non Connecté>")
      self.ui.cmbPort.setEnabled(True)
      self.ui.cmbBauds.setEnabled(True)
      self.ui.btnConnect.setText("Connecter") # La prochaine action du bouton sera pour connecter

  def on_cmbPort_changed(self):
    self.setConnectControlsStatus()

  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      self.logGrbl.append(self.ui.txtGCode.text().upper())
      self.__grblCom.sendLine(self.ui.txtGCode.text())
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
      self.logGrbl.append(">" + retour)

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
