# Makefile for cn5X++

#''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#                                                                         '
# Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
#                                                                         '
# This file is part of cn5X++                                             '
#                                                                         '
# cn5X++ is free software: you can redistribute it and/or modify it       '
#  under the terms of the GNU General Public License as published by      '
# the Free Software Foundation, either version 3 of the License, or       '
# (at your option) any later version.                                     '
#                                                                         '
# cn5X++ is distributed in the hope that it will be useful, but           '
# WITHOUT ANY WARRANTY; without even the implied warranty of              '
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           '
# GNU General Public License for more details.                            '
#                                                                         '
# You should have received a copy of the GNU General Public License       '
# along with this program.  If not, see <http://www.gnu.org/licenses/>.   '
#                                                                         '
#''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

#-----------------------------------------------------------------------
# Compile les fichiers .ui de QT Designer vers scripts Python
# Compile les fichiers de ressources vers scripts Python
#-----------------------------------------------------------------------

SRC=$(wildcard *.ts)
QMFILES=$(SRC:.ts=.qm)

all: $(QMFILES)

%.qm: %.ts
	lrelease cn5X.pro

%.ts: ../*.py cn5X.pro
	pylupdate5 cn5X.pro

