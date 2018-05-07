# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlgAPropos.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgApropos(object):
  def setupUi(self, dlgApropos):
    dlgApropos.setObjectName("dlgApropos")
    dlgApropos.setWindowModality(QtCore.Qt.ApplicationModal)
    dlgApropos.resize(590, 320)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/cn5X/images/XYZAB.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    dlgApropos.setWindowIcon(icon)
    dlgApropos.setSizeGripEnabled(False)
    dlgApropos.setModal(True)
    self.verticalLayout_3 = QtWidgets.QVBoxLayout(dlgApropos)
    self.verticalLayout_3.setObjectName("verticalLayout_3")
    self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
    self.horizontalLayout_2.setObjectName("horizontalLayout_2")
    self.frame = QtWidgets.QFrame(dlgApropos)
    self.frame.setObjectName("frame")
    self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
    self.verticalLayout_2.setContentsMargins(0, -1, -1, -1)
    self.verticalLayout_2.setObjectName("verticalLayout_2")
    self.label = QtWidgets.QLabel(self.frame)
    self.label.setMaximumSize(QtCore.QSize(178, 141))
    self.label.setText("")
    self.label.setPixmap(QtGui.QPixmap(":/cn5X/images/XYZAB.svg"))
    self.label.setScaledContents(True)
    self.label.setAlignment(QtCore.Qt.AlignCenter)
    self.label.setWordWrap(False)
    self.label.setObjectName("label")
    self.verticalLayout_2.addWidget(self.label)
    spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout_2.addItem(spacerItem)
    self.horizontalLayout_2.addWidget(self.frame)
    self.verticalLayout = QtWidgets.QVBoxLayout()
    self.verticalLayout.setObjectName("verticalLayout")
    self.label_2 = QtWidgets.QLabel(dlgApropos)
    self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.label_2.setObjectName("label_2")
    self.verticalLayout.addWidget(self.label_2)
    spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout.addItem(spacerItem1)
    self.lblVersion = QtWidgets.QLabel(dlgApropos)
    self.lblVersion.setObjectName("lblVersion")
    self.verticalLayout.addWidget(self.lblVersion)
    spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout.addItem(spacerItem2)
    self.label_3 = QtWidgets.QLabel(dlgApropos)
    self.label_3.setAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignTop)
    self.label_3.setWordWrap(True)
    self.label_3.setObjectName("label_3")
    self.verticalLayout.addWidget(self.label_3)
    spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    self.verticalLayout.addItem(spacerItem3)
    self.horizontalLayout_2.addLayout(self.verticalLayout)
    self.verticalLayout_3.addLayout(self.horizontalLayout_2)
    self.horizontalLayout = QtWidgets.QHBoxLayout()
    self.horizontalLayout.setSpacing(0)
    self.horizontalLayout.setObjectName("horizontalLayout")
    spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    self.horizontalLayout.addItem(spacerItem4)
    self.buttonBox = QtWidgets.QDialogButtonBox(dlgApropos)
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
    self.buttonBox.setObjectName("buttonBox")
    self.horizontalLayout.addWidget(self.buttonBox)
    self.verticalLayout_3.addLayout(self.horizontalLayout)

    self.retranslateUi(dlgApropos)
    self.buttonBox.accepted.connect(dlgApropos.accept)
    self.buttonBox.rejected.connect(dlgApropos.reject)
    QtCore.QMetaObject.connectSlotsByName(dlgApropos)

  def retranslateUi(self, dlgApropos):
    _translate = QtCore.QCoreApplication.translate
    dlgApropos.setWindowTitle(_translate("dlgApropos", "A propos de cn5X++"))
    self.label_2.setText(_translate("dlgApropos", "<h1>cn5X++</h1>"))
    self.lblVersion.setText(_translate("dlgApropos", "Version 0.0"))
    self.label_3.setText(_translate("dlgApropos", "CN5X++ est une application de panneau de contrôle 5/6 axes pour les machines à commandes numériques pilotées par Grbl. Cette application a pour but d\'implémenter toutes les fonctionalités du microprogramme grbl-Mega-5X.\n"
"\n"
"Copyright (C) Gauthier Brière."))

import cn5X_rc
