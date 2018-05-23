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

PYUIC=pyuic5
PYUICFLAGS=-di2
PYRCC=pyrcc5
PYRCCFLAGS=
LANG_DIR=i18n

all: *.py ressources lang

ressources: cn5X_rc.py

lang: $(LANG_DIR)/*.qm
	@(cd $(LANG_DIR) && $(MAKE))

%.qm: %.ts cn5X.pro

%.py: %.ui
	$(PYUIC) $(PYUICFLAGS) $< -o $@

%_rc.py: %.qrc
	$(PYRCC) $(PYRCCFLAGS) $< -o $@

