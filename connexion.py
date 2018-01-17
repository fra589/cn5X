# -*- coding: UTF-8 -*-

import serial
import serial.tools.list_ports
import time

class serialCom:
  # Communications serie entre le programme et GRBL
  def __init__(self, port="", bauds=115200):
    # Liste des ports gérés par le système
    serialCom.comList = serial.tools.list_ports.comports()
    serialCom.comList.sort()
    serialCom.baudRates = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    # Le port utilisé pour la communication
    self.comPort = serial.Serial()
    dir(self.comPort)
    self.comPort.port = port
    self.comPort.baudrate = bauds
    self.comPort.parity = serial.PARITY_NONE
    self.comPort.bytesize = serial.EIGHTBITS
    self.comPort.stopbits = serial.STOPBITS_ONE

  def connect(self):
    # Méthode pour connecter le port série sélectionné précédemment
    if not self.comPort.is_open:
      print(self.comPort.port)
      print(self.comPort.baudrate)
      self.comPort.open()
      print("Port ouvert...")
      time.sleep(2) # Attend l'initialisation
      print("leaving...")
    else:
      print("Déjà connecté !")

  def disconnect(self):
    # Méthode pour connecter le port série sélectionné précédemment
    if self.comPort.is_open:
      self.comPort.close()
    else:
      print("Pas connecté !")

