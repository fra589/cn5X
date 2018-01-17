#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys, os
from PyQt5 import QtWidgets, QtGui
import mainWindow
from connexion import *
from msgbox import *

defaultBaudRate = 115200

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)
    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)

    pathname = os.path.abspath(os.path.dirname(sys.argv[0]))
    os.chdir(pathname)

    # Chargement de la police des labels de status machine
    QtGui.QFontDatabase.addApplicationFont('fonts/LEDCalculator.ttf')

    # gestion du port série
    self.serial = serialCom()

    # Label du bouton connect
    self.ui.btnConnect.setText("Connecter")

    # on rempli la liste des ports série
    self.ui.cmbPort.addItem("")
    if len(serialCom.comList) > 0:
      for p in serialCom.comList:
        self.ui.cmbPort.addItem(p.device + ' - ' + p.description)
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

    # Et la liste des vitesses
    curIndex = -1
    for v in serialCom.baudRates:
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == defaultBaudRate:
        self.ui.cmbBauds.setCurrentIndex(curIndex)
        print(self.ui.cmbBauds.currentIndex())

    # on affiche un texte en bas de la fenêtre (status bar)
    self.ui.statusBar.showMessage("coucou")

    # Evenements du bouton d'arrêt d'urgence
    self.ui.btnUrgence.pressed.connect(self.action_arretUrgence)
    # un clic sur un élément de la liste appellera la méthode 'on_item_changed'
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed)

    # Connexions de routines du menu application
    self.ui.mnuAppOuvrir.triggered.connect(self.on_mnuAppOuvrir)
    self.ui.mnuAppQuitter.triggered.connect(self.on_mnuAppQuitter)
    # un clic sur le bouton "(De)Connecter" appellera la méthode 'action_btnConnect'
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)

  def on_mnuAppOuvrir(self):
    pass

  def on_mnuAppQuitter(self):
    self.ui.statusBar.showMessage("Bye-bye...")
    print("Bye-bye...")
    self.close()

  def action_arretUrgence(self):
    print("Arrêt d'urgence détecté !")
    if not(self.ui.btnUrgence.isChecked()):
      print("On est en train de stoper !!!")
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
      self.ui.btnStart.setEnabled(False)
      self.ui.btnStop.setEnabled(False)
      self.ui.btnUrgence.setToolTip("Dévérouiller l'arrêt d'urgence")
    else:
      print("On relance :-)")
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgence.svg'))
      self.ui.btnStart.setEnabled(True)
      self.ui.btnStop.setEnabled(True)
      self.ui.btnUrgence.setToolTip("Arrêt d'urgence")


  def action_btnConnect(self):
    if self.ui.btnConnect.text() == "Connecter":
      print('Appui bouton Connecter.')
      # Recupère les éléments du port à connecter
      serialDevice = self.ui.cmbPort.currentText()
      serialDevice = serialDevice.split("-")
      serialDevice = serialDevice[0].strip()
      self.serial.comPort.port = serialDevice
      self.serial.connect()
      self.ui.ptxtDebug.appendPlainText("Coucou")
      self.ui.btnConnect.setText("Déconnecter") # La prochaine action du bouton sera pour déconnecter
    else:
      print('Appui bouton Déconnecter.')
      self.serial.disconnect()
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

if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
