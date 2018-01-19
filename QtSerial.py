# -*- coding: UTF-8 -*-

from PyQt5 import QtCore
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class QSerialComm:
  """ Gestion des communications serie avec GRBL """
  def __init__(self, port="", bauds=115200):
    self.lePort = QSerialPort()
    self.lePort.setPortName(port)
    self.lePort.setBaudRate(bauds)
    self.lePort.setDataBits(QSerialPort.Data8)
    self.lePort.setStopBits(QSerialPort.OneStop)
    self.lePort.setParity(QSerialPort.NoParity)
    self.lePort._connected = False

  def portsList():
    """ Retourne la liste des ports disponibles sur le système """
    return(QSerialPortInfo.availablePorts())

  def baudRates():
    """ Renvoie la liste des vitesses standards """
    return(QSerialPortInfo.standardBaudRates())

  def isConnected(self):
    """ Renvoie l'etat de connexion du port """
    return self.lePort._connected

  def connect(self):
    """ Connexion du port """
    if not self.lePort._connected:
      RC = self.lePort.open(QtCore.QIODevice.ReadWrite)
      self.lePort._connected = True
      return RC

  def disconnect(self):
    """ Déconnexion du port """
    if self.lePort._connected:
      self.lePort.close()
      self.lePort._connected = False
