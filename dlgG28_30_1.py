# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlgG28_30_1.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgG28_30_1(object):
  def setupUi(self, dlgG28_30_1):
    dlgG28_30_1.setObjectName("dlgG28_30_1")
    dlgG28_30_1.resize(403, 304)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/cn5X/images/XYZAB.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    dlgG28_30_1.setWindowIcon(icon)
    self.gridLayout_2 = QtWidgets.QGridLayout(dlgG28_30_1)
    self.gridLayout_2.setContentsMargins(4, 4, 4, 4)
    self.gridLayout_2.setSpacing(4)
    self.gridLayout_2.setObjectName("gridLayout_2")
    self.lblPosition = QtWidgets.QLabel(dlgG28_30_1)
    self.lblPosition.setObjectName("lblPosition")
    self.gridLayout_2.addWidget(self.lblPosition, 0, 0, 1, 2)
    self.frmMPos = QtWidgets.QFrame(dlgG28_30_1)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.frmMPos.sizePolicy().hasHeightForWidth())
    self.frmMPos.setSizePolicy(sizePolicy)
    self.frmMPos.setMinimumSize(QtCore.QSize(0, 0))
    self.frmMPos.setStyleSheet("background-color: rgb(248, 255, 192);\n"
"color: rgb(0, 0, 63);")
    self.frmMPos.setFrameShape(QtWidgets.QFrame.Box)
    self.frmMPos.setObjectName("frmMPos")
    self.gridLayout = QtWidgets.QGridLayout(self.frmMPos)
    self.gridLayout.setContentsMargins(4, 0, 0, 0)
    self.gridLayout.setSpacing(0)
    self.gridLayout.setObjectName("gridLayout")
    self.lblLblPosX = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosX.sizePolicy().hasHeightForWidth())
    self.lblLblPosX.setSizePolicy(sizePolicy)
    self.lblLblPosX.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosX.setFont(font)
    self.lblLblPosX.setText("X")
    self.lblLblPosX.setObjectName("lblLblPosX")
    self.gridLayout.addWidget(self.lblLblPosX, 0, 0, 1, 1)
    self.lblPosX = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosX.sizePolicy().hasHeightForWidth())
    self.lblPosX.setSizePolicy(sizePolicy)
    self.lblPosX.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosX.setFont(font)
    self.lblPosX.setText("+00000.000")
    self.lblPosX.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosX.setObjectName("lblPosX")
    self.gridLayout.addWidget(self.lblPosX, 0, 1, 1, 1)
    self.chkPosX = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosX.setFont(font)
    self.chkPosX.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosX.setText("")
    self.chkPosX.setIconSize(QtCore.QSize(24, 24))
    self.chkPosX.setCheckable(True)
    self.chkPosX.setChecked(True)
    self.chkPosX.setObjectName("chkPosX")
    self.gridLayout.addWidget(self.chkPosX, 0, 2, 1, 1)
    self.lblLblPosY = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosY.sizePolicy().hasHeightForWidth())
    self.lblLblPosY.setSizePolicy(sizePolicy)
    self.lblLblPosY.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosY.setFont(font)
    self.lblLblPosY.setText("Y")
    self.lblLblPosY.setObjectName("lblLblPosY")
    self.gridLayout.addWidget(self.lblLblPosY, 1, 0, 1, 1)
    self.lblPosY = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosY.sizePolicy().hasHeightForWidth())
    self.lblPosY.setSizePolicy(sizePolicy)
    self.lblPosY.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosY.setFont(font)
    self.lblPosY.setText("+00000.000")
    self.lblPosY.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosY.setObjectName("lblPosY")
    self.gridLayout.addWidget(self.lblPosY, 1, 1, 1, 1)
    self.chkPosY = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosY.setFont(font)
    self.chkPosY.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosY.setText("")
    self.chkPosY.setIconSize(QtCore.QSize(24, 24))
    self.chkPosY.setCheckable(True)
    self.chkPosY.setChecked(True)
    self.chkPosY.setObjectName("chkPosY")
    self.gridLayout.addWidget(self.chkPosY, 1, 2, 1, 1)
    self.lblLblPosZ = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosZ.sizePolicy().hasHeightForWidth())
    self.lblLblPosZ.setSizePolicy(sizePolicy)
    self.lblLblPosZ.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosZ.setFont(font)
    self.lblLblPosZ.setText("Z")
    self.lblLblPosZ.setObjectName("lblLblPosZ")
    self.gridLayout.addWidget(self.lblLblPosZ, 2, 0, 1, 1)
    self.lblPosZ = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosZ.sizePolicy().hasHeightForWidth())
    self.lblPosZ.setSizePolicy(sizePolicy)
    self.lblPosZ.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosZ.setFont(font)
    self.lblPosZ.setText("+00000.000")
    self.lblPosZ.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosZ.setObjectName("lblPosZ")
    self.gridLayout.addWidget(self.lblPosZ, 2, 1, 1, 1)
    self.chkPosZ = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosZ.setFont(font)
    self.chkPosZ.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosZ.setText("")
    self.chkPosZ.setIconSize(QtCore.QSize(24, 24))
    self.chkPosZ.setCheckable(True)
    self.chkPosZ.setChecked(True)
    self.chkPosZ.setObjectName("chkPosZ")
    self.gridLayout.addWidget(self.chkPosZ, 2, 2, 1, 1)
    self.lblLblPosA = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosA.sizePolicy().hasHeightForWidth())
    self.lblLblPosA.setSizePolicy(sizePolicy)
    self.lblLblPosA.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosA.setFont(font)
    self.lblLblPosA.setText("A")
    self.lblLblPosA.setObjectName("lblLblPosA")
    self.gridLayout.addWidget(self.lblLblPosA, 3, 0, 1, 1)
    self.lblPosA = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosA.sizePolicy().hasHeightForWidth())
    self.lblPosA.setSizePolicy(sizePolicy)
    self.lblPosA.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosA.setFont(font)
    self.lblPosA.setText("+00000.000")
    self.lblPosA.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosA.setObjectName("lblPosA")
    self.gridLayout.addWidget(self.lblPosA, 3, 1, 1, 1)
    self.chkPosA = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosA.setFont(font)
    self.chkPosA.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosA.setText("")
    self.chkPosA.setIconSize(QtCore.QSize(24, 24))
    self.chkPosA.setCheckable(True)
    self.chkPosA.setChecked(True)
    self.chkPosA.setObjectName("chkPosA")
    self.gridLayout.addWidget(self.chkPosA, 3, 2, 1, 1)
    self.lblLblPosB = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosB.sizePolicy().hasHeightForWidth())
    self.lblLblPosB.setSizePolicy(sizePolicy)
    self.lblLblPosB.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosB.setFont(font)
    self.lblLblPosB.setText("B")
    self.lblLblPosB.setObjectName("lblLblPosB")
    self.gridLayout.addWidget(self.lblLblPosB, 4, 0, 1, 1)
    self.lblPosB = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosB.sizePolicy().hasHeightForWidth())
    self.lblPosB.setSizePolicy(sizePolicy)
    self.lblPosB.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosB.setFont(font)
    self.lblPosB.setText("+00000.000")
    self.lblPosB.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosB.setObjectName("lblPosB")
    self.gridLayout.addWidget(self.lblPosB, 4, 1, 1, 1)
    self.chkPosB = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosB.setFont(font)
    self.chkPosB.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosB.setText("")
    self.chkPosB.setIconSize(QtCore.QSize(24, 24))
    self.chkPosB.setCheckable(True)
    self.chkPosB.setChecked(True)
    self.chkPosB.setObjectName("chkPosB")
    self.gridLayout.addWidget(self.chkPosB, 4, 2, 1, 1)
    self.lblLblPosC = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblLblPosC.sizePolicy().hasHeightForWidth())
    self.lblLblPosC.setSizePolicy(sizePolicy)
    self.lblLblPosC.setMaximumSize(QtCore.QSize(16777215, 16777215))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblLblPosC.setFont(font)
    self.lblLblPosC.setText("C")
    self.lblLblPosC.setObjectName("lblLblPosC")
    self.gridLayout.addWidget(self.lblLblPosC, 5, 0, 1, 1)
    self.lblPosC = QtWidgets.QLabel(self.frmMPos)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(3)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblPosC.sizePolicy().hasHeightForWidth())
    self.lblPosC.setSizePolicy(sizePolicy)
    self.lblPosC.setMinimumSize(QtCore.QSize(0, 0))
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.lblPosC.setFont(font)
    self.lblPosC.setText("+00000.000")
    self.lblPosC.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
    self.lblPosC.setObjectName("lblPosC")
    self.gridLayout.addWidget(self.lblPosC, 5, 1, 1, 1)
    self.chkPosC = QtWidgets.QCheckBox(self.frmMPos)
    font = QtGui.QFont()
    font.setFamily("LED Calculator")
    font.setPointSize(20)
    self.chkPosC.setFont(font)
    self.chkPosC.setStyleSheet("QCheckBox{margin-left: 6px;}\n"
"QCheckBox::indicator{\n"
"  width: 24px;\n"
"  height: 24px;\n"
"}\n"
"QCheckBox::indicator:unchecked {\n"
"    image: url(:/cn5X/images/chkBoxUnChecked.svg);\n"
"}\n"
"QCheckBox::indicator:checked {\n"
"    image: url(:/cn5X/images/chkBoxChecked.svg);\n"
"}")
    self.chkPosC.setText("")
    self.chkPosC.setIconSize(QtCore.QSize(24, 24))
    self.chkPosC.setCheckable(True)
    self.chkPosC.setChecked(True)
    self.chkPosC.setObjectName("chkPosC")
    self.gridLayout.addWidget(self.chkPosC, 5, 2, 1, 1)
    self.gridLayout_2.addWidget(self.frmMPos, 1, 0, 1, 3)
    self.imageDeco = QtWidgets.QPushButton(dlgG28_30_1)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.imageDeco.sizePolicy().hasHeightForWidth())
    self.imageDeco.setSizePolicy(sizePolicy)
    self.imageDeco.setText("")
    icon1 = QtGui.QIcon()
    icon1.addPixmap(QtGui.QPixmap(":/cn5X/images/questionG28.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    self.imageDeco.setIcon(icon1)
    self.imageDeco.setIconSize(QtCore.QSize(48, 48))
    self.imageDeco.setAutoDefault(False)
    self.imageDeco.setFlat(True)
    self.imageDeco.setObjectName("imageDeco")
    self.gridLayout_2.addWidget(self.imageDeco, 2, 0, 1, 1)
    self.lblMessage = QtWidgets.QLabel(dlgG28_30_1)
    self.lblMessage.setWordWrap(True)
    self.lblMessage.setObjectName("lblMessage")
    self.gridLayout_2.addWidget(self.lblMessage, 2, 1, 1, 2)
    self.chkDontShow = QtWidgets.QCheckBox(dlgG28_30_1)
    self.chkDontShow.setObjectName("chkDontShow")
    self.gridLayout_2.addWidget(self.chkDontShow, 3, 0, 1, 2)
    self.buttonBox = QtWidgets.QDialogButtonBox(dlgG28_30_1)
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Yes)
    self.buttonBox.setObjectName("buttonBox")
    self.gridLayout_2.addWidget(self.buttonBox, 3, 2, 1, 1)

    self.retranslateUi(dlgG28_30_1)
    QtCore.QMetaObject.connectSlotsByName(dlgG28_30_1)

  def retranslateUi(self, dlgG28_30_1):
    _translate = QtCore.QCoreApplication.translate
    dlgG28_30_1.setWindowTitle(_translate("dlgG28_30_1", "Define G28.1 absolute position"))
    self.lblPosition.setText(_translate("dlgG28_30_1", "Current machine position (MPos)"))
    self.chkPosX.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.chkPosY.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.chkPosZ.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.chkPosA.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.chkPosB.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.chkPosC.setToolTip(_translate("dlgG28_30_1", "Uncheck to keep this axis at its current position"))
    self.lblMessage.setText(_translate("dlgG28_30_1", "Save the current machine position (MPos) in the G28.1 Grbl\'s location?"))
    self.chkDontShow.setText(_translate("dlgG28_30_1", "Don\'t show confirmation again"))

import cn5X_rc
