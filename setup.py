#! /usr/bin/env python3
# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018-2019 Gauthier Brière (gauthier.briere "at" gmail.com)    '
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
                    include_files = ['COPYING',
                                      ('i18n/flags/flag_fr.svg', 'i18n/flags/flag_fr.svg'),
                                      ('i18n/flags/flag_en.svg', 'i18n/flags/flag_en.svg'),
                                      ('i18n/flags/flag_es.svg', 'i18n/flags/flag_es.svg'),
                                      ('i18n/flags/flag_pt.svg', 'i18n/flags/flag_pt.svg'),
                                      ('i18n/cn5X.fr.qm', 'i18n/cn5X.fr.qm'),
                                      ('i18n/cn5X.en.qm', 'i18n/cn5X.en.qm'),
                                      ('i18n/cn5X.es.qm', 'i18n/cn5X.es.qm'),
                                      ('i18n/cn5X.pt.qm', 'i18n/cn5X.pt.qm'),
                                      ('i18n/cn5X_locales.xml', 'i18n/cn5X_locales.xml'),
                                      ('i18n/cn5X_locales.xsd', 'i18n/cn5X_locales.xsd')
                                    ]
                    )

import sys
base = 'Win32GUI' if sys.platform=='win32' else None



executables = [
    Executable('cn5X.py', base=base)
]

setup(name='cn5X++',
      version = APP_VERSION_STRING,
      description = '5/6 axis Grbl control panel for grbl-Mega-5X',
      options = dict(build_exe = buildOptions),
      executables = executables)
