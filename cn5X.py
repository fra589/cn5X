#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, os, datetime
from PyQt5 import QtCore, QtGui, QtWidgets
import mainWindow
from msgbox import *
from QtSerial import QSerialComm
from grblDecode import grblDecode

defaultBaudRate = 115200

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)
    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)

    self.timerDblClic = QtCore.QTimer()
    self.decode = grblDecode(self.ui)

    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    print(pathname)
    os.chdir(pathname)

    """---------- Préparation de l'interface ----------"""
    QtGui.QFontDatabase.addApplicationFont(pathname + "/fonts/LEDCalculator.ttf") # Chargement de la police des labels de status machine
    self.ui.btnConnect.setText("Connecter")                                       # Label du bouton connect
    self.serial = QSerialComm()                                                   # Création Objet pour communications
    self.ui.cmbPort.addItem("")                                                   # On rempli la liste des ports série
    if len(QSerialComm.portsList()) > 0:
      for p in QSerialComm.portsList():
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
    if self.ui.cmbPort.currentText() == "":
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setEnabled(False)
    else:
      self.ui.cmbBauds.setEnabled(True)
      self.ui.btnConnect.setEnabled(True)

    curIndex = -1                                                                  # On rempli la liste des vitesses
    for v in QSerialComm.baudRates():
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == defaultBaudRate:
        self.ui.cmbBauds.setCurrentIndex(curIndex)

    # on affiche une chaine vide texte en bas de la fenêtre (status bar)
    self.ui.statusBar.showMessage("")

    """---------- Connections des évennements traités ----------"""
    self.ui.btnUrgence.pressed.connect(self.arretUrgence)                # Evenements du bouton d'arrêt d'urgence
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed) # un clic sur un élément de la liste appellera la méthode 'on_item_changed'
    self.ui.mnuAppOuvrir.triggered.connect(self.on_mnuAppOuvrir)         # Connexions des routines du menu application
    self.ui.mnuAppQuitter.triggered.connect(self.on_mnuAppQuitter)
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)           # un clic sur le bouton "(De)Connecter" appellera la méthode 'action_btnConnect'
    self.ui.btnSend.pressed.connect(self.sendCmd)                        # Bouton d'envoi de commandes unitaires
    self.ui.txtGCode.returnPressed.connect(self.sendCmd)                 # Même fonction par la touche entrée
    self.serial.lePort.readyRead.connect(self.readSerial) # gestion du port série


  def on_mnuAppOuvrir(self):
    pass

  def on_mnuAppQuitter(self):
    self.ui.statusBar.showMessage("Bye-bye...")
    print("Bye-bye...")
    self.close()

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
      self.serial.lePort.setPortName(serialDevice)
      print("Appel de la connexion")
      self.serial.connect()
      print("Connexion effectuée")
      self.ui.lblConnectStatus.setText("Connecté à " + serialDevice)
      self.ui.cmbPort.setEnabled(False)
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
    else:
      print('Appui bouton Déconnecter.')
      self.serial.disconnect()
      self.ui.lblConnectStatus.setText("<Non Connecté>")
      self.ui.cmbPort.setEnabled(True)
      self.ui.cmbBauds.setEnabled(True)
      self.ui.btnConnect.setText("Connecter") # La prochaine action du bouton sera pour connecter

  def on_cmbPort_changed(self):
    print(self.ui.cmbPort.currentIndex())
    print(self.ui.cmbPort.currentText())
    if self.ui.cmbPort.currentText() == "":
      self.ui.cmbBauds.setEnabled(False)
      self.ui.btnConnect.setEnabled(False)
    else:
      self.ui.cmbBauds.setEnabled(True)
      self.ui.btnConnect.setEnabled(True)

  def sendCmd(self):
    if self.ui.txtGCode.text() != "":
      buffWrite = bytes(self.ui.txtGCode.text() + "\n", sys.getdefaultencoding())
      self.serial.lePort.write(buffWrite)
      self.ui.txtGCode.setSelection(0,len(self.ui.txtGCode.text()))

  def readSerial(self):
    print("Lecture des données...")
    s = ''
    #nWait = self.serial.lePort.bytesAvailable()
    #while nWait > 0:
    while self.serial.lePort.canReadLine():
      #buff = self.serial.lePort.readAll()
      buff = self.serial.lePort.readLine()
      s += bytes(buff).decode()
      #print("Nouveau buffer = [", s, "]", sep='')
      nWait = self.serial.lePort.bytesAvailable()
    # Decoupe des lignes unitaires
    s = s.splitlines()
    # Envoie les chaines reçues au décodage pour mise à jour de l'interface
    for l in s:
      if l != "":
        l = self.decode.setReply(l)
      # Ajoute le texte reçu dans la console
      self.ui.ptxtDebug.setPlainText(self.ui.ptxtDebug.toPlainText() + l + "\n")
    # Place le curseur en fin de texte de la console
    cursor = self.ui.ptxtDebug.textCursor();
    cursor.movePosition(QtGui.QTextCursor.End);
    self.ui.ptxtDebug.setTextCursor(cursor)

if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
