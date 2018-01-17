#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from PyQt5 import QtWidgets, QtGui
import mainWindow
from connexion import *

defaultBaudRate = 115200

class winMain(QtWidgets.QMainWindow):

  def __init__(self, parent=None):
    QtWidgets.QMainWindow.__init__(self, parent)
    self.ui = mainWindow.Ui_mainWindow()
    self.ui.setupUi(self)

    # gestion du port série
    self.serial = serialCom()

    # Evenements du bouton d'arrêt d'urgence
    self.ui.btnUrgence.pressed.connect(self.action_arretUrgence)
    
    # Label du bouton connect
    self.ui.btnConnect.setText("Connecter")
    # un clic sur le bouton appellera la méthode 'action_bouton'
    self.ui.btnConnect.clicked.connect(self.action_btnConnect)

    # on rempli la liste des ports série
    for p in serialCom.comList:
      self.ui.cmbPort.addItem(p.device + ' - ' + p.description)
    # Et la liste des vitesses
    curIndex = -1
    for v in serialCom.baudRates:
      self.ui.cmbBauds.addItem(str(v))
      curIndex += 1
      if v == defaultBaudRate:
        self.ui.cmbBauds.setCurrentIndex(curIndex)
        print(self.ui.cmbBauds.currentIndex())

    # un clic sur un élément de la liste appellera la méthode 'on_item_changed'
    self.ui.cmbPort.currentIndexChanged.connect(self.on_cmbPort_changed)

    # on affiche un texte en bas de la fenêtre (status bar)
    self.ui.statusBar.showMessage("coucou")

  def action_arretUrgence(self):
    print("Arrêt d'urgence détecté !")
    if not(self.ui.btnUrgence.isChecked()):
      print("On est en train de stoper !!!")
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgenceOff.svg'))
    else:
      print("On relance :-)")
      self.ui.btnUrgence.setIcon(QtGui.QIcon('images/btnUrgence.svg'))

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

if __name__ == '__main__':
  import sys
  app = QtWidgets.QApplication(sys.argv)
  window = winMain()
  window.show()
  sys.exit(app.exec_())
