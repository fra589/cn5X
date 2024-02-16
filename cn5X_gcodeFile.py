# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_gcodeFile.py is part of cn5X++                          '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
'  under the terms of the GNU General Public License as published by      '
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

import os, sys
from datetime import datetime
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QCoreApplication, QObject, pyqtSignal, pyqtSlot, QModelIndex, QItemSelectionModel, QSettings
from PyQt6.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QListView
from cn5X_config import *
from msgbox import *
from grblCom import grblCom
from cn5X_toolChange import dlgToolChange
from cn5X_gcodeParser import gcodeParser

class gcodeFile(QObject):
  '''
  Gestion d'un fichier GCode dans la QListView de l'interface graphique reservee a cet usage
  Methodes :
  - __init__(QListView) -> Initialise et definit les elements de l'UI qui recevront le contenu du fichier
  - showFileOpen()        -> Affiche la boite de dialogue d'ouverture
  - showFileSave()        -> Affiche la boite de dialogue d'enregistrement
  - readFile(filePath)    -> Charge un fichier dans la QListView
  - saveFile(filePath)    -> Enregistre le contenu de la QListView dans un fichier
  - closeFile()           -> Vide la QListView
  - setGcodeChanged(bool) -> Definit si le contenu de la liste a ete modifie depuis la lecture ou l'enregistrement du fichier
  - bool = gcodeChanged() -> Renvoi vrai si le contenu de la liste a ete modifie depuis la lecture ou l'enregistrement du fichier
  '''

  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant

  def __init__(self, ui, gcodeFileUi: QListView, dialogToolChange: dlgToolChange):
    super().__init__()
    self.__filePath         = ""
    self.__ui               = ui
    self.__gcodeFileUi      = gcodeFileUi
    self.__gcodeFileUiModel = QStandardItemModel(self.__gcodeFileUi)
    self.__gcodeFileUiModel.itemChanged.connect(self.on_gcodeChanged)
    self.__dlgToolChange = dialogToolChange

    self.__gcodeCharge      = False
    self.__gcodeChanged     = False

    self.__settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)
    self.__toolNumber    = 0
    self.__firstToolDone = False

    self.__gcodeParser = gcodeParser()

  def showFileOpen(self):
    ''' Affiche la boite de dialogue d'ouverture '''
    fileDialog = QtWidgets.QFileDialog(None)
    opt = fileDialog.options()
    lastDir = self.__settings.value("Files/lastGCodeFileDir", "")
    if lastDir != "":
      fileDialog.setDirectory(lastDir)
    fName = fileDialog.getOpenFileName(None, self.tr("Open a GCode file"), "", self.tr("GCode file (*.gcode *.ngc *.nc *.gc *.cnc)"), options=opt)
    if fName[0] != "":
      # Memorise le dernier répertoire utilisé
      lastDir = os.path.dirname(fName[0])
      self.__settings.setValue("Files/lastGCodeFileDir", lastDir)
      # Met à jour la liste des 10 derniers fichiers utilisés
      # Récupère la liste dans les settings
      lastFiles = self.getLastFileList()
      # Recherche si le fichier est déja dans la liste
      if fName[0] in lastFiles:
        # S'il l'est déjà, on le supprime
        lastFiles.remove(fName[0])
      # On l'insert en première position de la liste
      lastFiles.insert(0, fName[0])
      # Sauvegarde la nouvelle liste
      self.saveLastFileList(lastFiles)

      '''
      for i in range(9, 0, -1):
        settingName1 = "Files/lastFile{}".format(i)
        settingName2 = "Files/lastFile{}".format(i-1)
        self.__settings.setValue(settingName1, self.__settings.value(settingName2, ""))
      self.__settings.setValue("Files/lastFile0", fName[0])
      '''
    # Renvoi le fichier à ouvrir
    return fName

  def getLastFileList(self):
    ''' Retrouve la liste des 10 derniers fichiers'''
    liste = []
    for i in range(10):
      settingName = "Files/lastFile{}".format(i)
      liste.append(self.__settings.value(settingName, ""))
    return liste

  def saveLastFileList(self, fileList):
    i = 0
    for f in fileList:
      if i < 10:
        settingName = "Files/lastFile{}".format(i)
        self.__settings.setValue(settingName, f)
        i = i + 1

  def readFile(self, filePath: str):
    self.sig_log.emit(logSeverity.info.value, self.tr("Reading file: {}").format(filePath))
    try:
      f = open(filePath,'r')
      lignes  = f.readlines()
      f.close()
      self.sig_log.emit(logSeverity.info.value, self.tr("{} lines in the file").format(len(lignes)))
      # Envoi du contenu dans la liste
      self.__gcodeFileUiModel.clear()
      for l in lignes:
        item = QStandardItem(l.strip())
        self.__gcodeFileUiModel.appendRow(item)
      self.__gcodeFileUi.setModel(self.__gcodeFileUiModel)
      # Selectionne la premiere ligne du fichier dans la liste
      self.selectGCodeFileLine(0)
      # Selectionne l'onglet du fichier
    except Exception as e:
      self.sig_log.emit(logSeverity.error.value, self.tr("Reading file error: {}").format(filePath))
      self.sig_log.emit(logSeverity.error.value, str(e))
      self.__gcodeFileUiModel.clear()
      self.__filePath     = ""
      self.__gcodeChanged = False
      return False

    # Pas d'erreur
    self.__gcodeCharge = True
    self.__filePath     = filePath
    self.__gcodeChanged = False
    return True


  def isFileLoaded(self):
    return self.__gcodeCharge


  def filePath(self):
    return self.__filePath


  def fileName(self):
    return os.path.basename(self.__filePath)


  def selectGCodeFileLine(self, num: int):
    ''' Selectionne un element de la liste du fichier GCode '''
    idx = self.__gcodeFileUiModel.index(num, 0, QModelIndex())
    self.__gcodeFileUi.selectionModel().clearSelection()
    self.__gcodeFileUi.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectionFlag.SelectCurrent)


  def getGCodeSelectedLine(self):
    ''' Renvoie le N° (0 base) de la ligne selectionnee dans la liste GCode et les donnees de cette ligne. '''
    idx = self.__gcodeFileUi.selectionModel().selectedIndexes()
    return [idx[0].row(), self.__gcodeFileUiModel.data(idx[0])]


  def saveAs(self):
    fName = self.showFileSave()
    if fName[0] != "":
      self.sig_log.emit(logSeverity.info.value, self.tr("saveAs({})").format(fName[0]))
      self.saveFile(fName[0])
    else:
      self.sig_log.emit(logSeverity.info.value, self.tr("saveAs() canceled!"))


  def showFileSave(self):
    ''' Affiche la boite de dialogue "Save as" '''
    fileDialog = QtWidgets.QFileDialog(None)
    opt = fileDialog.options()
    opt |= QtWidgets.QFileDialog.Option.DontUseNativeDialog
    fName = QtWidgets.QFileDialog.getSaveFileName(None, self.tr("Save GCode file"), "", self.tr("GCode file (*.gcode *.ngc *.nc *.gc *.cnc)"), options=opt)
    return fName


  def saveFile(self, filePath: str = ""):
    if filePath == "":
      if self.__filePath == "":
        # Le nom du fichier n'est pas definit, il n'y a pas de fichier charge, donc, rien a sauvegarder !
        return
      else:
        filePath = self.__filePath
    self.sig_log.emit(logSeverity.info.value, self.tr("Saving file: {}").format(filePath))
    try:
      f = open(filePath, 'w')
      for I in range(self.__gcodeFileUiModel.rowCount()):
        idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
        if self.__gcodeFileUiModel.data(idx) != "":
          f.write(self.__gcodeFileUiModel.data(idx) + '\n')
      f.close()
      self.__filePath = filePath
    except Exception as e:
      self.sig_log.emit(logSeverity.error.value, self.tr("Save file error: {}").format(filePath))
      self.sig_log.emit(logSeverity.error.value, str(e))
    # Supprime les lignes vides dans la grille d'affichage
    self.delEmptyRow()
    # Reinit du flag fichier change
    self.__gcodeChanged = False


  def enQueue(self, com: grblCom, startLine: int = 0, endLine: int = -1):
    """ Envoi des lignes de startLine a endLine dans la file d'attente du grblCom """

    # Force le curseur souris sablier
    QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    if endLine == -1:
      endLine = self.__gcodeFileUiModel.rowCount()

    for I in range(startLine, endLine + 1):
      idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
      if self.__gcodeFileUiModel.data(idx) != "":
        gcodeLine = self.__gcodeFileUiModel.data(idx)
        if gcodeLine is not None:
          dico  = self.__gcodeParser.wordDict(gcodeLine)
          wlist = self.__gcodeParser.wordList(gcodeLine)

          if ('T' in dico):
            # Appel d'outil, on memorise le nouvel (ou futur) outil
            # actif et on en force l'envoi vers Grbl.
            try:
              self.__toolNumber = int(float(dico['T']))
            except ValueError as e:
              # Erreur sur la valeur de T non numérique ou absente
              self.sig_log.emit(logSeverity.error.value, self.tr("enQueue(): Invalid tool number (T) value '{}'.").format(dico['T']))
              self.__toolNumber = 0
            com.gcodePush("T{}".format(self.__toolNumber))
            self.sig_log.emit(logSeverity.info.value, self.tr("enQueue(): Select tool number T{}.").format(self.__toolNumber))

          if ("M6" in wlist):
            # Demande de changement d'outil.
            # La commande M6 ne sera pas envoyée à Grbl
            if self.useToolChange():
              # Traitement des changements d'outil manuels
              if self.ignoreFirstToolChange() and not self.__firstToolDone:
                # Ignore le premier changement d'outil du programme
                # Si l'option est active, l'opérateur est sensé avoir
                # déjà monté le premier outil avant le début de l'usinage
                # donc, on ne fait rien (on trace juste dans la log)
                self.sig_log.emit(logSeverity.info.value, self.tr("Ignoring first tool change (T{}).").format(self.__toolNumber))
              else:
                # Appel de la boite de dialogue de changement d'outil
                RC = self.toolChange(self.__toolNumber)
                if RC == QtWidgets.QDialog.Rejected:
                  # Annulation du changement d'outil, on arrête le flux. 
                  # Restore le curseur souris sablier en fin d'envoi
                  QtWidgets.QApplication.restoreOverrideCursor()
                  return False
              if not self.__firstToolDone:
                # Mémorise que le premier changement d'outil à eu lieu
                self.__firstToolDone = True
          else:
            # Les autres commandes que M6 sont envoyées à Grbl 
            com.gcodePush(gcodeLine)

          # Force une mise à jour des status GCode
          com.gcodePush(CMD_GRBL_GET_GCODE_STATE, COM_FLAG_NO_OK)

    # Restore le curseur souris sablier en fin d'envoi
    QtWidgets.QApplication.restoreOverrideCursor()


  def delEmptyRow(self):
    """ Elimination des lignes GCode vides """
    for I in reversed(range(self.__gcodeFileUiModel.rowCount())):
      # On commence par la fin pour pouvoir supprimer sans tout decaler pour la suite
      idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
      if self.__gcodeFileUiModel.data(idx) == "":
        self.__gcodeFileUiModel.removeRow(I)


  def deleteGCodeFileLine(self, num: int):
    self.__gcodeFileUiModel.removeRow(num)
    self.__gcodeChanged = True


  def insertGCodeFileLine(self, num: int):
    item = QStandardItem("")
    self.__gcodeFileUiModel.insertRow(num, item)


  def addGCodeFileLine(self, num: int):
    item = QStandardItem("")
    self.__gcodeFileUiModel.insertRow(num+1, item)


  def showConfirmChangeLost(self):
    m = msgBox(
                  title     = self.tr("Save Changes"),
                  text      = self.tr("Do you want to save the changes before closing?"),
                  info      = self.tr("If you do not save, any changes made since opening or the last save will be lost."),
                  icon      = msgIconList.Question,
                  stdButton = msgButtonList.Save | msgButtonList.Cancel | msgButtonList.Discard,
                  defButton = msgButtonList.Save,
                  escButton = msgButtonList.Cancel
    )
    return (m.afficheMsg())


  def closeFile(self):
    if self.__gcodeChanged:
      # GCode modifie, on demande confirmation
      Ret = self.showConfirmChangeLost()
      if Ret == msgButtonList.Save:
        if self.__filePath == "":
          filePath = self.showFileSave()
          if filePath == "":
            # Annulation de la boite de dialogue
            return False
          else:
            self.__filePath = filePath
        self.saveFile(self.__filePath)
        return True
      elif Ret == msgButtonList.Discard:
        # Fermer le fichier consiste en vider la fenetre GCode
        self.__gcodeFileUiModel.clear()
        self.__gcodeChanged = False
        self.__gcodeCharge  =False
        return True
      else: # Ret == msgButtonList.Cancel:
        return False
    else:
      # GCode non modifie, on ferme sans confirmation
      # Fermer le fichier consiste en vider la fenetre GCode
      # et a supprimer le status GCode charge.
      self.__gcodeFileUiModel.clear()
      self.__gcodeChanged = False
      self.__gcodeCharge  =False
      return True


  @pyqtSlot("QStandardItem*")
  def on_gcodeChanged(self, item):
    self.__gcodeChanged = True


  def gcodeChanged(self):
    return self.__gcodeChanged


  def setGcodeChanged(self, value:bool):
    self.__gcodeChanged = value


  def toolChange(self, toolNum: int):
    ''' Appel de la boite de dialogue de changement d'outils '''
    RC = self.__dlgToolChange.showDialog(toolNum)
    if RC == QtWidgets.QDialog.Accepted:
      self.sig_log.emit(logSeverity.info.value, self.tr("Tool change (T{}) done.").format(toolNum))
    else: # RC = QtWidgets.QDialog.Rejected
      self.sig_log.emit(logSeverity.warning.value, self.tr("Tool change (T{}) canceled.").format(toolNum))
    return RC


  def useToolChange(self):
    return self.__settings.value("useToolChange", True, type=bool)


  def ignoreFirstToolChange(self):
    return self.__settings.value("ignoreFirstToolChange", False, type=bool)


