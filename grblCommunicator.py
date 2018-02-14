# -*- coding: UTF-8 -*-

import sys, time
from math import *
from PyQt5.QtCore import QCoreApplication, QObject, QThread, QTimer, QEventLoop, pyqtSignal, pyqtSlot, QIODevice
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class grblCommunicator(QObject):
  """
  Objet servant à la communication avec grbl
  2 sous classes sont utilisées :
  - serialCommunicator : pour la lecture et l'écriture depuis et vers le port série,
  - serialTimer : timer qui intéroge grbl (?) à interval régulier pour tenir à jour la position et l'état du grbl,
  chacune de ces 2 classes vivant dans son propre thread.
  """

  # Définition des signaux externes
  sig_msg          = pyqtSignal(str)
  sig_init         = pyqtSignal(str) # Emis à la réception de la chaine d'initialisation de Grbl
  sig_grblOk       = pyqtSignal()    # Grbl Responses "ok"
  sig_grblResponse = pyqtSignal(str) # Grbl Responses "error:X" ou "ALARM:X"
  sig_grblStatus   = pyqtSignal(str) # < > : Enclosed chevrons contains status report data.
  sig_data_recived = pyqtSignal(str) # Other Push Messages from Grbl
  sig_data_debug   = pyqtSignal(str) # All data from Grbl


  # Définition des signaux internes
  sig_abort_serial = pyqtSignal()
  sig_serial_send  = pyqtSignal(str, bool)
  sig_abort_timer  = pyqtSignal()
  sig_start_timer  = pyqtSignal()
  sig_stop_timer   = pyqtSignal()

  def __init__(self):
    super().__init__()
    self.__threads = None
    self.__timer1Delay = 40 # Millisecondes
    self.__Com = None

  def startCommunicator(self, comPort: str, baudRate: int):
    '''
    Gestion des communications série et des timers dans des threads distincts
    '''
    self.__threads = []
    # Lance le serialCommunicator dans un thread distinct
    self.sig_msg.emit('grblCommunicator: Starting serialCommunicator thread.')
    communicator = serialCommunicator(comPort, baudRate)
    thread = QThread()
    thread.setObjectName('serialCommunicator')
    self.__threads.append((thread, communicator))  # need to store worker too otherwise will be gc'd
    communicator.moveToThread(thread)
    # Connecte les signaux du communicator
    communicator.sig_msg.connect(self.sig_msg.emit)               # Message de fonctionnements du communicator
    communicator.sig_init.connect(self.sig_init.emit)             # Message d'initialisation de Grbl transmis
    communicator.sig_ok.connect(self.sig_grblOk.emit)                 # Reponses Grbl "ok" transmises
    communicator.sig_response.connect(self.sig_grblResponse.emit) # Reponses Grbl "error:X" ou "ALARM:X" transmises
    communicator.sig_status.connect(self.sig_grblStatus.emit)     # Transmission Status Grbl
    communicator.sig_data.connect(self.sig_data_recived.emit)     # Autres données reçues de Grbl
    communicator.sig_data_debug.connect(self.sig_data_debug.emit)
    communicator.sig_done.connect(self.on_communicator_close)     # Emis à la fin du thread du communicator
    communicator.sig_send_ok.connect(self.on_send_ok)             # Données envoyées
    # control du communicator :
    self.sig_serial_send.connect(communicator.sendData)
    self.sig_abort_serial.connect(communicator.abort)
    # Start the thread...
    thread.started.connect(communicator.run)
    thread.start()  # this will emit 'started' and start thread's event loop
    self.__Com = communicator

    # Lance le serialTimer dans un thread distinct
    self.sig_msg.emit('grblCommunicator: Starting serialTimer thread.')
    timer1 = serialTimer(self.__timer1Delay, communicator)
    thread = QThread()
    thread.setObjectName('serialTimer1')
    self.__threads.append((thread, timer1))  # need to store worker too otherwise will be gc'd
    timer1.moveToThread(thread)
    # Connecte les signaux du timer1
    timer1.sig_msg.connect(self.sig_msg.emit)             # Message de fonctionnements du timer1
    timer1.sig_serialTimer.connect(communicator.sendData) # Passe le top timer au communicator pour envoi sur le port serie
    timer1.sig_done.connect(self.on_timer1_close)         # Emis à la fin du thread du timer1
    # control du timer1
    communicator.sig_grbl_ok.connect(timer1.start)
    self.sig_start_timer.connect(timer1.start)
    self.sig_stop_timer.connect(timer1.stop)
    self.sig_abort_timer.connect(timer1.abort)
    # Start the thread...
    thread.started.connect(timer1.run)
    thread.start()

  def startTimer(self):
    self.sig_start_timer.emit()

  def stopTimer(self):
    self.sig_stop_timer.emit()

  def stopCommunicator(self):
    self.sig_msg.emit("Envoi signal sig_abort_timer...")
    self.sig_stop_timer.emit()
    self.sig_abort_timer.emit()
    self.sig_msg.emit("Envoi signal sig_abort_serial...")
    self.sig_abort_serial.emit()
    # Attente de la fin des threads
    for thread, worker in self.__threads:  # note nice unpacking by Python, avoids indexing
        thread.quit()  # this will quit **as soon as thread event loop unblocks**
        thread.wait()  # <- so you need to wait for it to *actually* quit
    self.sig_msg.emit("Thread(s) enfant(s) terminé(s).")

  @pyqtSlot()
  def on_communicator_close(self):
    self.sig_msg.emit('grblCommunicator: serialCommunicator closed.')

  @pyqtSlot()
  def on_send_ok(self):
    pass

  @pyqtSlot()
  def on_timer1_close(self):
    self.sig_msg.emit('grblCommunicator: serialTimer closed.')

  @pyqtSlot(str, bool)
  def sendData(self, buff: str, trapOk: bool = False):
    self.sig_serial_send.emit(buff, trapOk)

  @pyqtSlot(str, bool)
  def sendLine(self, buff: str, trapOk: bool = False):
    # Force la fin de ligne
    if buff[-1:] != '\n':
      self.sig_serial_send.emit(buff + '\n', trapOk)
    else:
      self.sig_serial_send.emit(buff, trapOk)

class serialCommunicator(QObject):
  """
  Worker must derive from QObject in order to emit signals,
  connect slots to other signals, and operate in a QThread.
  """
  sig_msg        = pyqtSignal(str) # Messages de fonctionnements
  sig_init       = pyqtSignal(str) # Emis à la réception de la chaine d'initialisation de Grbl
  sig_grbl_ok    = pyqtSignal()    # Emis quand Grbl à fini son initialisation
  sig_ok         = pyqtSignal()    # Reponses "ok"
  sig_response   = pyqtSignal(str) # Reponses "error:X" ou "ALARM:X"
  sig_status     = pyqtSignal(str) # Status "<***>"
  sig_data       = pyqtSignal(str) # Emis à chaque autre ligne de données reçue
  sig_data_debug = pyqtSignal(str) # All data from Grbl
  sig_send_ok    = pyqtSignal()    # Emis à chaque ligne envoyée
  sig_done       = pyqtSignal()    # Emis à la fin du thread

  def __init__(self, comPort: str, baudRate: int):
    super().__init__()
    self.__abort      = False
    self.__portName   = comPort
    self.__baudRate   = baudRate
    self.__okToSend   = False
    self.__grblStatus = ""
    self.__okTrap     = 0

  @pyqtSlot()
  def run(self):
    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_msg.emit('Running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    # Configuration du port série
    self.__comPort = QSerialPort()
    self.__comPort.setPortName(self.__portName)
    self.__comPort.setBaudRate(self.__baudRate)
    self.__comPort.setDataBits(QSerialPort.Data8)
    self.__comPort.setStopBits(QSerialPort.OneStop)
    self.__comPort.setParity(QSerialPort.NoParity)

    # Ouverture du port série
    RC = False
    try:
      RC = self.__comPort.open(QIODevice.ReadWrite)
    except OSError as err:
      self.sig_msg.emit("serialCommunicator : Erreur ouverture du port : {0}".format(err))
    except:
      self.sig_msg.emit("serialCommunicator : Unexpected error : {}".format(sys.exc_info()[0]))

    if RC:
      self.sig_msg.emit("serialCommunicator : Ouverture comPort {} : RC = {}".format(self.__comPort.portName(), RC))
    else:
      self.sig_msg.emit("serialCommunicator : Erreur à l'ouverture du port série : err# = {0}".format(self.__comPort.error()))


    # Boucle de lecture du port série
    s = ''
    while 1:
      if self.__comPort.waitForReadyRead(20):
        ###print("Lecture du port série")
        buff = self.__comPort.readAll()
        try:
          s += buff.data().decode()
          # Découpe les données reçues en lignes pour les envoyer une par une
          t = s.splitlines()
        except:
          self.sig_msg.emit("serialCommunicator : Erreur décodage : {}".format(sys.exc_info()[0]))
          s = ''
        if s != '':
          if s[-1] == "\n":
            # La dernière ligne est complette, on envoi tout
            for l in t:
              self.traileLaLigne(l)
            s=''
          else:
            # La dernière ligne est incomplette, on envoi jusqu'à l'avant dernière.
            for l in t[:-1]:
              self.traileLaLigne(l)
            # On laisse la derniere ligne dans le buffer pour qu'elle soit complettée.
            s = t[-1]
      else:
        ###print(".", end="")
        pass
      # Process events to receive signals;
      QCoreApplication.processEvents()
      if self.__abort:
        self.sig_msg.emit("serialCommunicator : aborting...")
        break

    # Sortie de la boucle de lecture
    self.sig_msg.emit("serialCommunicator : Fermeture du port série.")
    self.__comPort.close()
    # Emission du signal de fin
    self.sig_done.emit()

  def traileLaLigne(self, l):
    # Envoi de toutes les lignes dans le debug
    self.sig_data_debug.emit(l)
    # Grbl 1.1f ['$' for help] (Init string)
    if l[:5] == "Grbl " and l[-5:] == "help]":
      self.__okToSend = True
      self.__grblStatus = "Idle"
      self.sig_msg.emit("serialCommunicator : Grbl prêt pour recevoir des données")
      self.sig_init.emit(l)
      self.sig_grbl_ok.emit()
    elif l[:1] == "<" and l[-1:] == ">": # Real-time Status Reports
      if self.__grblStatus != l[1:-1].split("|")[0]:
        self.__grblStatus = l[1:-1].split("|")[0]
      self.sig_status.emit(l)
    elif l == "ok": # Reponses "ok"
      if self.__okTrap > 0:
        self.__okTrap -= 1
      else:
        self.sig_ok.emit()
    elif l[:6] == "error:" or l[:6] == "ALARM:": # "error:X" ou ALARM:X
      self.sig_response.emit(l)
    else:
      self.sig_data.emit(l)

  @pyqtSlot()
  def isOkToSend(self):
    return self.__okToSend

  @pyqtSlot()
  def grblStatus(self):
    return self.__grblStatus

  @pyqtSlot(str, bool)
  def sendData(self, buff: str, trapOk: bool = False):
    if not self.__okToSend:
      self.sig_msg.emit("serialCommunicator : Erreur : Grbl pas prêt pour recevoir des données")
      return

    if trapOk:
      self.__okTrap += 1 # La prochaine réponse "ok" de Grbl ne sera pas transmise

    ###print("Sending [{}]".format(buff))
    buffWrite = bytes(buff, sys.getdefaultencoding())
    # Temps nécessaire pour la com (millisecondes)
    t_calcul = ceil(1000 * len(buffWrite) * 8 / self.__baudRate) # Arrondi à l'entier supérieur
    timeout = 10 + (2 * t_calcul) # 2 fois le temps nécessaire + 10 millisecondes
    self.__comPort.write(buffWrite)
    if self.__comPort.waitForBytesWritten(timeout):
      self.sig_send_ok.emit()
    else:
      self.sig_msg.emit("serialCommunicator : Erreur envoi des données : timeout")

  @pyqtSlot()
  def abort(self):
    self.sig_msg.emit("serialCommunicator : abort reçu.")
    self.__abort = True

class serialTimer(QObject):

  sig_msg         = pyqtSignal(str) # Messages de fonctionnements
  sig_serialTimer = pyqtSignal(str, bool) # Signal du timer
  sig_done        = pyqtSignal()    # Emis à la fin du thread

  def __init__(self, signalPeriod: int, communicator: serialCommunicator):
    super().__init__()
    self.__sigPeriod = signalPeriod
    self.__Actif = False
    self.__loop = None
    self.__communicator = communicator

  @pyqtSlot()
  def run(self):
    thread_name = QThread.currentThread().objectName()
    thread_id = int(QThread.currentThreadId())  # cast to int() is necessary
    self.sig_msg.emit('serialTimer : Running "{}" from thread #{}.'.format(thread_name, hex(thread_id)))

    self.__serialTimer1 = QTimer()
    self.__serialTimer1.timeout.connect(self.serialTimer1Send)
    self.__serialTimer2 = QTimer()
    self.__serialTimer2.timeout.connect(self.serialTimer2Send)
    self.__serialTimer3 = QTimer()
    self.__serialTimer3.timeout.connect(self.serialTimer3Send)
    self.__Actif = False
    self.__loop = QEventLoop()
    self.__loop.exec_()

  @pyqtSlot()
  def stop(self):
    if self.__Actif:
      self.sig_msg.emit("serialTimer : stopping timers.")
      self.__serialTimer1.stop()
      self.__serialTimer2.stop()
      self.__serialTimer3.stop()
      self.__Actif = False
    else:
      self.sig_msg.emit("serialTimer : timer not running.")

  @pyqtSlot()
  def start(self):
    if not self.__Actif:
      self.sig_msg.emit("serialTimer : starting timers.")
      sleepTime = self.__sigPeriod / 1000
      self.__serialTimer1.start(self.__sigPeriod)
      time.sleep(sleepTime / 2)
      self.__serialTimer2.start(self.__sigPeriod*4)
      time.sleep(sleepTime)
      self.__serialTimer3.start(self.__sigPeriod*4)
      self.__Actif = True
    else:
      self.sig_msg.emit("serialTimer : timers already running.")

  @pyqtSlot()
  def abort(self):
    self.sig_msg.emit("serialTimer : quit timer...")
    self.__serialTimer1.stop()
    self.__serialTimer2.stop()
    self.__serialTimer3.stop()
    self.__Actif = False
    self.__loop.quit()
    self.sig_done.emit()

  @pyqtSlot()
  def isActif(self):
    return self._Actif

  @pyqtSlot()
  def serialTimer1Send(self):
    self.sig_serialTimer.emit("?", False)

  @pyqtSlot()
  def serialTimer2Send(self):
    self.sig_serialTimer.emit("$G\n", True)

  @pyqtSlot()
  def serialTimer3Send(self):
    if self.__communicator.grblStatus() == "Idle":
      self.sig_serialTimer.emit("$#\n", True)
    else:
      print("communicator.grblStatus = ", self.__communicator.grblStatus())
