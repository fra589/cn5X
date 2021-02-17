# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlgHelpProbe.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgHelpProbe(object):
  def setupUi(self, dlgHelpProbe):
    dlgHelpProbe.setObjectName("dlgHelpProbe")
    dlgHelpProbe.resize(648, 576)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(":/cn5X/images/XYZAB.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    dlgHelpProbe.setWindowIcon(icon)
    self.verticalLayout = QtWidgets.QVBoxLayout(dlgHelpProbe)
    self.verticalLayout.setContentsMargins(4, 4, 4, 4)
    self.verticalLayout.setSpacing(6)
    self.verticalLayout.setObjectName("verticalLayout")
    self.lblContent = QtWidgets.QLabel(dlgHelpProbe)
    sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(self.lblContent.sizePolicy().hasHeightForWidth())
    self.lblContent.setSizePolicy(sizePolicy)
    self.lblContent.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.lblContent.setWordWrap(True)
    self.lblContent.setObjectName("lblContent")
    self.verticalLayout.addWidget(self.lblContent)
    self.buttonBox = QtWidgets.QDialogButtonBox(dlgHelpProbe)
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
    self.buttonBox.setObjectName("buttonBox")
    self.verticalLayout.addWidget(self.buttonBox)

    self.retranslateUi(dlgHelpProbe)
    self.buttonBox.accepted.connect(dlgHelpProbe.close)
    self.buttonBox.rejected.connect(dlgHelpProbe.close)
    QtCore.QMetaObject.connectSlotsByName(dlgHelpProbe)

  def retranslateUi(self, dlgHelpProbe):
    _translate = QtCore.QCoreApplication.translate
    dlgHelpProbe.setWindowTitle(_translate("dlgHelpProbe", "cn5X++ - Probing help"))
    self.lblContent.setText(_translate("dlgHelpProbe", "<html><head/><body><h1 align=\"center\">Probe detection of single axis.</h1><p style=\"color: #8b0000; font-weight: bold;\">Attention! Measuring operations are very intolerant of incorrect settings. It is strongly recommended to do preliminary tests on loose object that will not damage the probe when unexpected movements. It is recommended to carefully check each setting before measuring the workpiece.</p><p><i>The trajectory of the probe by the example of measurement of axis X+:</i></p><p>If the \"Seek rate\" option is checked, the probing will be made in 2 times:<br />- A first probing with \"Length\" probing distance at \"Seek rate\" speed, the retract of \"Pull-off dist.\" distance,<br />- A second probing with \"Pull-off dist.\" probing distance at \"Feed rate\" speed.</p><p align=\"center\"><img src=\":/doc/doc/probeSingleAxis.svg\"/></p><p>If the \"Seek rate\" option is unchecked, there will be only one probing with \"Length\" probe distance at \"Feed rate\" speed</p><p>Due to the Grbl\'s acceleration/deceleration planning, when probing, the tool is stopped a small amount after the point. When checking the \"Move after probe\" option, the tool will be moved either exactly on the probed point, or retracted by a \"Retract\" length from the result of the check.</p></body></html>"))

import cn5X_rc
