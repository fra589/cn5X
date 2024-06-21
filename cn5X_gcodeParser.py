# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file: cn5X_gcodeParser.py, is part of cn5X++                       '
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

from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from cn5X_config import *

LINE_FLAG_OVERFLOW            = 1
LINE_FLAG_COMMENT_PARENTHESES = 2
LINE_FLAG_COMMENT_SEMICOLON   = 4


class gcodeParser(QObject):
  '''
  Analyse d'une ligne de GCode
  '''

  sig_log     = pyqtSignal(int, str) # Message de fonctionnement du composant

  def __init__(self):
    super().__init__()


  @pyqtSlot(str)
  def noComment(self, gcodeLine: str):
    '''
    Suprimme le(s) commentaire(s) et les espaces de la ligne GCode.
    Utilisation du même algorithme (protocol.c) que Grbl pour la
    supression des commentaires et des espaces dans la ligne.
    '''
    line = ""
    line_flags = 0
    for c in gcodeLine:
      if line_flags:
        if (c == ')'):
          # End of '()' comment. Resume line allowed.
          if (line_flags & LINE_FLAG_COMMENT_PARENTHESES):
            line_flags &= ~(LINE_FLAG_COMMENT_PARENTHESES)
      else:
        if (c <= ' '):
          # Throw away whitepace and control characters
          pass
        elif (c == '/'):
          # Block delete NOT SUPPORTED. Ignore character.
          pass
        elif (c == '('):
          # Enable comments flag and ignore all characters until ')' or EOL.
          # NOTE: This doesn't follow the NIST definition exactly, but is good enough for now.
          line_flags |= LINE_FLAG_COMMENT_PARENTHESES;
        elif (c == ';'):
          # NOTE: ';' comment to EOL is a LinuxCNC definition. Not NIST.
          line_flags |= LINE_FLAG_COMMENT_SEMICOLON;
        else:
          # Ajout du caractère à la ligne
          line += c.upper();
    return line


  @pyqtSlot(str)
  def wordDict(self, gcodeLine: str):
    '''
    Renvoi un dictionnaire des mots GCode contenus dans la ligne
    Sous la forme {'mot': 'valeurs', 'mot': 'valeurs', ...}
    '''
    words = dict()
    currentWord  = ""
    currentValue = ""
    for c in self.noComment(gcodeLine):
      if c in VALIDES_GCODE_WORDS:
        if currentWord != "":
          # Ajoute le mot courant au dictionnaire avant de passer au suivant
          words[currentWord] = currentValue
          currentValue = ""
        # C'est le nouveau mot courant nouveau mot
        currentWord = c
      else:
        currentValue += c
    # Ajoute le dernier mot
    words[currentWord] = currentValue
    # Revoi le résultat
    return words


  @pyqtSlot(str)
  def wordList(self, gcodeLine: str):
    '''
    Renvoi une liste des mots GCode contenus dans la ligne avec leurs valeurs
    '''
    liste = []
    currentWord  = ""
    currentValue = ""
    for c in self.noComment(gcodeLine):
      if c in VALIDES_GCODE_WORDS:
        if currentWord != "":
          # Ajoute le mot courant au la liste avant de passer au suivant
          liste.append(currentWord + currentValue)
          currentValue = ""
        # C'est le nouveau mot courant nouveau mot
        currentWord = c
      else:
        currentValue += c
    # Ajoute le dernier mot
    liste.append(currentWord + currentValue)
    # Revoi le résultat
    return liste










