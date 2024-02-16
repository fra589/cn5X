#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2024 Gauthier Brière (gauthier.briere "at" gmail.com)    '
'                                                                         '
' This file is part of cn5X++                                             '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it       '
' under the terms of the GNU General Public License as published by       '
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

from cn5X_config import *
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [],
                    include_files = ['COPYING']
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None



executables = [
    Executable('cn5X.py', base=base)
]

setup(name='cn5X++',
  version = APP_VERSION_STRING,
  description = '5/6 axis Grbl control panel for grbl-Mega-5X',
  author = 'Gauthier Brière',
  install_requires = [
    'pyqt6',
    'pyserial',
    'pyqt6.qtmultimedia',
    ],
  options = dict(build_exe = buildOptions),
  executables = executables
  )
