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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QModelIndex, QItemSelectionModel
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QListView
from cn5X_config import *
from msgbox import *


class gcodeFile(QObject):
  '''
  Gestion d'un fichier GCode dans la QListView de l'interface graphique réservée à cet usage
  Méthodes :
  - __init__(QListView) -> Initialise et définit les éléments de l'UI qui recevront le contenu du fichier
  - showFileOpen()        -> Affiche la boite de dialogue d'ouverture
  - showFileSave()        -> Affiche la boite de dialogue d'enregistrement
  - readFile(filePath)    -> Charge un fichier dans la QListView
  - saveFile(filePath)    -> Enregistre le contenu de la QListView dans un fichier
  - closeFile()           -> Vide la QListView
  - setGcodeChanged(bool) -> Définit si le contenu de la liste à été modifié depuis la lecture ou l'enregistrement du fichier
  - bool = gcodeChanged() -> Renvoi vrai si le contenu de la liste à été modifié depuis la lecture ou l'enregistrement du fichier
  '''

  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant

  def __init__(self, gcodeFileUi: QListView):
    super().__init__()
    self.__filePath         = ""
    self.__gcodeFileUi      = gcodeFileUi
    self.__gcodeFileUiModel = QStandardItemModel(self.__gcodeFileUi)
    self.__gcodeFileUiModel.itemChanged.connect(self.on_gcodeChanged)
    self.__gcodeCharge      = False
    self.__gcodeChanged     = False

  def showFileOpen(self):
    # Affiche la boite de dialogue d'ouverture
    opt = QtWidgets.QFileDialog.Options()
    opt |= QtWidgets.QFileDialog.DontUseNativeDialog
    fileName = QtWidgets.QFileDialog.getOpenFileName(None, "Ouvrir un fichier GCode", "", "Fichier GCode (*.gcode *.ngc *.nc *.gc *.cnc)", options=opt)
    return fileName

  def showFileSave(self):
    pass

  def readFile(self, filePath: str):
    self.sig_log.emit(logSeverity.info.value, "Lecture du fichier : {}".format(filePath))
    try:
      f = open(filePath,'r')
      lignes  = f.readlines()
      f.close()
      self.sig_log.emit(logSeverity.info.value, "{} lignes dans le fichier".format(len(lignes)))
      # Envoi du contenu dans la liste
      self.__gcodeFileUiModel.clear()
      for l in lignes:
        item = QStandardItem(l.strip())
        self.__gcodeFileUiModel.appendRow(item)
      self.__gcodeFileUi.setModel(self.__gcodeFileUiModel)
      # Sélectionne la premiere ligne du fichier dans la liste
      self.__selectGCodeFileLine(0)
      # Sélectionne l'onglet du fichier
    except Exception as e:
      self.sig_log.emit(logSeverity.error.value, "Erreur lecture du fichier : {}".format(filePath))
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

  def filePath():
    return self.__filePath

  def __selectGCodeFileLine(self, num: int):
    # Selectionne un élément de la liste du fichier GCode
    idx = self.__gcodeFileUiModel.index(num, 0, QModelIndex())
    self.__gcodeFileUi.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectCurrent)

  def getGCodeSelectedLine(self):
    ''' Renvoie le N° (0 base) de la ligne sélectionnée dans la liste GCode et les données de cette ligne. '''
    idx = self.__gcodeFileUi.selectionModel().selectedIndexes()
    return [idx[0].row(), self.__gcodeFileUiModel.data(idx[0])]

  def saveFile(self, filePath: str = ""):

    if filePath == "":
      if self.__filePath == "":
        # Le nom du fichier n'est pas définit, il n'y à pas de fichier chargé, donc, rien à sauvegarder !
        return()
      else:
        filePath = self.__filePath
    self.sig_log.emit(logSeverity.info.value, "Enregistrement du fichier : {}".format(filePath))
    try:
      f = open(filePath, 'w')
      for I in range(self.__gcodeFileUiModel.rowCount()):
        idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
        if self.__gcodeFileUiModel.data(idx) != "":
          f.write(self.__gcodeFileUiModel.data(idx) + '\n')
      f.close()
    except Exception as e:
      self.sig_log.emit(logSeverity.error.value, "Erreur Enregistrement du fichier : {}".format(filePath))
      self.sig_log.emit(logSeverity.error.value, str(e))
    # Supprime les lignes vides
    self.delEmptyRow()
    # Reinit du flag fichier changé
    self.__gcodeChanged = False


  def delEmptyRow(self):
    """ Elimination des lignes GCode vides """
    for I in reversed(range(self.__gcodeFileUiModel.rowCount())):
      # On commence par la fin pour pouvoir supprimer sans tout décaler pour la suite
      idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
      if self.__gcodeFileUiModel.data(idx) == "":
        print("Suppression de la ligne N° {}".format(I+1))
        self.__gcodeFileUiModel.removeRow(I)


  def showConfirmChangeLost(self):
    m = msgBox(
                  title     = "Enregistrer les modifications",
                  text      = "Voulez-vous enregistrer les modifications avant de fermer ?",
                  info      = "Si vous n'enregistrez pas, toutes les modifications effectuées depuis l'ouverture ou la dernière sauvegarde seront perdues.",
                  icon      = msgIconList.Question,
                  stdButton = msgButtonList.Save | msgButtonList.Cancel | msgButtonList.Discard,
                  defButton = msgButtonList.Save,
                  escButton = msgButtonList.Cancel
    )
    return(m.afficheMsg())


  def closeFile(self):
    if self.__gcodeChanged:
      # GCode modifié, on demande confirmation
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
        # Fermer le fichier consiste en vider la fenêtre GCode
        self.__gcodeFileUiModel.clear()
        self.__gcodeChanged = False
        self.__gcodeCharge  =False
        return True
      else: # Ret == msgButtonList.Cancel:
        return False
    else:
      # GCode non modifié, on ferme sans confirmation
      # Fermer le fichier consiste en vider la fenêtre GCode
      # et à supprimer le status GCode chargé.
      self.__gcodeFileUiModel.clear()
      self.__gcodeChanged = False
      self.__gcodeCharge  =False
      return True

  @pyqtSlot("QStandardItem*")
  def on_gcodeChanged(self, item):
    print("on_gcodeChanged()")
    self.__gcodeChanged = True

  def gcodeChanged(self):
    return self.__gcodeChanged

  def setGcodeChanged(self, value:bool):
    self.__gcodeChanged = value




