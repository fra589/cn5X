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

from PyQt5.QtWidgets import QMessageBox

class msgIconList:
  NoIcon = QMessageBox.NoIcon           # 0 the message box does not have any icon.
  Question = QMessageBox.Question       # 4 an icon indicating that the message is asking a question.
  Information = QMessageBox.Information # 1 an icon indicating that the message is nothing out of the ordinary.
  Warning = QMessageBox.Warning         # 2 an icon indicating that the message is a warning, but can be dealt with.
  Critical = QMessageBox.Critical       # 3 an icon indicating that the message represents a critical problem.

class msgButtonList:
  Ok = QMessageBox.Ok                           # 0x00000400  An "OK" button defined with the AcceptRole.
  Open = QMessageBox.Open                       # 0x00002000  An "Open" button defined with the AcceptRole.
  Save = QMessageBox.Save                       # 0x00000800  A "Save" button defined with the AcceptRole.
  Cancel = QMessageBox.Cancel                   # 0x00400000  A "Cancel" button defined with the RejectRole.
  Close = QMessageBox.Close                     # 0x00200000  A "Close" button defined with the RejectRole.
  Discard = QMessageBox.Discard                 # 0x00800000  A "Discard" or "Don't Save" button, depending on the platform, defined with the DestructiveRole.
  Apply = QMessageBox.Apply                     # 0x02000000  An "Apply" button defined with the ApplyRole.
  Reset = QMessageBox.Reset                     # 0x04000000  A "Reset" button defined with the ResetRole.
  RestoreDefaults = QMessageBox.RestoreDefaults # 0x08000000  A "Restore Defaults" button defined with the ResetRole.
  Help = QMessageBox.Help                       # 0x01000000  A "Help" button defined with the HelpRole.
  SaveAll = QMessageBox.SaveAll                 # 0x00001000  A "Save All" button defined with the AcceptRole.
  Yes = QMessageBox.Yes                         # 0x00004000  A "Yes" button defined with the YesRole.
  YesToAll = QMessageBox.YesToAll               # 0x00008000  A "Yes to All" button defined with the YesRole.
  No = QMessageBox.No                           # 0x00010000  A "No" button defined with the NoRole.
  NoToAll = QMessageBox.NoToAll                 # 0x00020000  A "No to All" button defined with the NoRole.
  Abort = QMessageBox.Abort                     # 0x00040000  An "Abort" button defined with the RejectRole.
  Retry = QMessageBox.Retry                     # 0x00080000  A "Retry" button defined with the AcceptRole.
  Ignore = QMessageBox.Ignore                   # 0x00100000  An "Ignore" button defined with the AcceptRole.
  NoButton = QMessageBox.NoButton               # 0x00000000  An invalid button.

class msgBox:
  def __init__(self,
               title="",
         text="",
         info="",
         detail="",
         icon=QMessageBox.NoIcon,
         stdButton=QMessageBox.Ok,
         defButton=QMessageBox.NoButton,
         escButton=QMessageBox.NoButton
        ):
    self.msg = QMessageBox()
    self.msg.setWindowTitle(title)
    self.msg.setText(text)
    self.msg.setInformativeText(info)
    self.msg.setDetailedText(detail)
    self.msg.setIcon(icon)
    self.msg.setStandardButtons(stdButton)
    self.msg.setDefaultButton(defButton)
    self.msg.setEscapeButton(escButton)

  def afficheMsg(self):
    return (self.msg.exec())
