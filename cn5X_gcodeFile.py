# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X++                                               '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it         '
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
'''
if sys.platform == 'linux':
  print("Platform = Linux")
  import gi
  gi.require_version('Gtk+', '3.0')
  from gi.repository import Gtk # => Segmentation fault. Conflit possible avec QT ?
'''
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QModelIndex, QItemSelectionModel
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QListView
from cn5X_config import *
from msgbox import *
from grblCom import grblCom


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

  def __init__(self, gcodeFileUi: QListView):
    super().__init__()
    self.__filePath         = ""
    self.__gcodeFileUi      = gcodeFileUi
    self.__gcodeFileUiModel = QStandardItemModel(self.__gcodeFileUi)
    self.__gcodeFileUiModel.itemChanged.connect(self.on_gcodeChanged)
    self.__gcodeCharge      = False
    self.__gcodeChanged     = False

  def showFileOpen(self):
    ''' Affiche la boite de dialogue d'ouverture '''
    '''
    if sys.platform == 'linux':
      # Prépare la boite de dialogue
      dialog = Gtk.FileChooserDialog(
        self.tr("Ouvrir un fichier GCode"),
        self,
        Gtk.FileChooserAction.OPEN,
        (
          Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
          Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
      )
      dialog.set_local_only(False) # Permet l'affichage des fichiers réseaux sous Linux GTK+3
      dialog_filter = Gtk.FileFilter()
      dialog_filter.set_name(self.tr("Fichier GCode"))
      dialog_filter.add_pattern("*.gcode")
      dialog_filter.add_pattern("*.ngc")
      dialog_filter.add_pattern("*.nc")
      dialog_filter.add_pattern("*.gc")
      dialog_filter.add_pattern("*.cnc")
      dialog.add_filter(dialog_filter)
      # Affiche la boite de dialogue
      response = dialog.run()
      # Traite la réponse
      if response == Gtk.ResponseType.OK:
          print("Open clicked")
          print("File selected: " + dialog.get_filename())
      elif response == Gtk.ResponseType.CANCEL:
          print("Cancel clicked")
      # Libère les ressources
      dialog.destroy()

    else: # sys.platform == 'linux'
    '''
    opt = QtWidgets.QFileDialog.Options()
    ###opt |= QtWidgets.QFileDialog.DontUseNativeDialog
    fName = QtWidgets.QFileDialog.getOpenFileName(None, self.tr("Ouvrir un fichier GCode"), "", self.tr("Fichier GCode (*.gcode *.ngc *.nc *.gc *.cnc)"), options=opt)
    return fName

  def readFile(self, filePath: str):
    self.sig_log.emit(logSeverity.info.value, self.tr("Lecture du fichier : {}").format(filePath))
    try:
      f = open(filePath,'r')
      lignes  = f.readlines()
      f.close()
      self.sig_log.emit(logSeverity.info.value, self.tr("{} lignes dans le fichier").format(len(lignes)))
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
      self.sig_log.emit(logSeverity.error.value, self.tr("Erreur lecture du fichier : {}").format(filePath))
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
    self.__gcodeFileUi.selectionModel().setCurrentIndex(idx, QItemSelectionModel.SelectCurrent)


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
      self.sig_log.emit(logSeverity.info.value, self.tr("saveAs() annule !"))


  def showFileSave(self):
    ''' Affiche la boite de dialogue "Save as" '''
    opt = QtWidgets.QFileDialog.Options()
    opt |= QtWidgets.QFileDialog.DontUseNativeDialog
    fName = QtWidgets.QFileDialog.getSaveFileName(None, self.tr("Enregistrer un fichier GCode"), "", self.tr("Fichier GCode (*.gcode *.ngc *.nc *.gc *.cnc)"), options=opt)
    return fName


  def saveFile(self, filePath: str = ""):
    if filePath == "":
      if self.__filePath == "":
        # Le nom du fichier n'est pas definit, il n'y a pas de fichier charge, donc, rien a sauvegarder !
        return
      else:
        filePath = self.__filePath
    self.sig_log.emit(logSeverity.info.value, self.tr("Enregistrement du fichier : {}").format(filePath))
    try:
      f = open(filePath, 'w')
      for I in range(self.__gcodeFileUiModel.rowCount()):
        idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
        if self.__gcodeFileUiModel.data(idx) != "":
          f.write(self.__gcodeFileUiModel.data(idx) + '\n')
      f.close()
      self.__filePath = filePath
    except Exception as e:
      self.sig_log.emit(logSeverity.error.value, self.tr("Erreur Enregistrement du fichier : {}").format(filePath))
      self.sig_log.emit(logSeverity.error.value, str(e))
    # Supprime les lignes vides dans la grille d'affichage
    self.delEmptyRow()
    # Reinit du flag fichier change
    self.__gcodeChanged = False


  def enQueue(self, com: grblCom, startLine: int = 0, endLine: int = -1):
    """ Envoi des lignes de startLine a endLine dans la file d'attente du grblCom """
    if endLine == -1:
      endLine = self.__gcodeFileUiModel.rowCount()
    for I in range(startLine, endLine + 1):
      idx = self.__gcodeFileUiModel.index( I, 0, QModelIndex())
      if self.__gcodeFileUiModel.data(idx) != "":
        com.gcodePush(self.__gcodeFileUiModel.data(idx))
        com.gcodePush(CMD_GRBL_GET_GCODE_STATE, COM_FLAG_NO_OK)


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
                  title     = self.tr("Enregistrer les modifications"),
                  text      = self.tr("Voulez-vous enregistrer les modifications avant de fermer ?"),
                  info      = self.tr("Si vous n'enregistrez pas, toutes les modifications effectuees depuis l'ouverture ou la derniere sauvegarde seront perdues."),
                  icon      = msgIconList.Question,
                  stdButton = msgButtonList.Save | msgButtonList.Cancel | msgButtonList.Discard,
                  defButton = msgButtonList.Save,
                  escButton = msgButtonList.Cancel
    )
    return(m.afficheMsg())


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

