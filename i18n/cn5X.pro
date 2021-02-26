# cn5X.pro
# QT Linguist translation project
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#'                                                                         '
#' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
#'                                                                         '
#' This file is part of cn5X++                                             '
#'                                                                         '
#' cn5X++ is free software: you can redistribute it and/or modify it       '
#'  under the terms of the GNU General Public License as published by      '
#' the Free Software Foundation, either version 3 of the License, or       '
#' (at your option) any later version.                                     '
#'                                                                         '
#' cn5X++ is distributed in the hope that it will be useful, but           '
#' WITHOUT ANY WARRANTY; without even the implied warranty of              '
#' MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           '
#' GNU General Public License for more details.                            '
#'                                                                         '
#' You should have received a copy of the GNU General Public License       '
#' along with this program.  If not, see <http://www.gnu.org/licenses/>.   '
#'                                                                         '
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Utiliser :
## cd $HOME/src/cn5X/i18n
## pylupdate5 cn5X.pro
# Pour mettre à jour les sources de traduction.

SOURCES += ../cn5X.py \
	../cn5X_apropos.py \
	../cn5X_config.py \
	../cn5X_gcodeFile.py \
	../cn5X_helpProbe.py \
	../cn5X_rc.py \
	../cnled.py \
	../cnQLabel.py \
	../cnQPushButton.py \
	../compilOptions.py \
	../dlgAPropos.py \
	../dlgConfig.py \
	../dlgG28_30_1.py \
	../dlgG92.py \
  ../dlgHelpProbe.py \
  ../dlgJog.py \
	../gcodeQLineEdit.py \
	../grblCom.py \
	../grblComSerial.py \
	../grblComStack.py \
	../grblConfig.py \
	../grblDecode.py \
	../grblError.py \
	../grblG28_30_1.py \
	../grblG92.py \
	../grblJog.py \
  ../grblProbe.py \
	../mainWindow.py \
	../msgbox.py \
	../qweditmask.py \
  ../qwprogressbox.py \
	../speedOverrides.py
TRANSLATIONS += cn5X.fr.ts \
                cn5X.en.ts


