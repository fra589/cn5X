# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qwHorloge.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_qwHorloge(object):
  def setupUi(self, qwHorloge):
    qwHorloge.setObjectName("qwHorloge")
    qwHorloge.resize(411, 101)
    self.lblFondHM = QtWidgets.QLabel(qwHorloge)
    self.lblFondHM.setGeometry(QtCore.QRect(0, 0, 331, 101))
    font = QtGui.QFont()
    font.setFamily("DSEG14 Classic")
    font.setPointSize(72)
    font.setItalic(True)
    self.lblFondHM.setFont(font)
    self.lblFondHM.setStyleSheet("color: rgb(16, 32, 16);\n"
"background-color: None;")
    self.lblFondHM.setTextFormat(QtCore.Qt.PlainText)
    self.lblFondHM.setAlignment(QtCore.Qt.AlignCenter)
    self.lblFondHM.setObjectName("lblFondHM")
    self.lblHM = QtWidgets.QLabel(qwHorloge)
    self.lblHM.setGeometry(QtCore.QRect(0, 0, 331, 101))
    font = QtGui.QFont()
    font.setFamily("DSEG14 Classic")
    font.setPointSize(72)
    font.setBold(False)
    font.setItalic(True)
    font.setWeight(50)
    self.lblHM.setFont(font)
    self.lblHM.setStyleSheet("color: rgb(127, 255, 127);\n"
"background-color: None;")
    self.lblHM.setTextFormat(QtCore.Qt.PlainText)
    self.lblHM.setAlignment(QtCore.Qt.AlignCenter)
    self.lblHM.setObjectName("lblHM")
    self.lblFondS = QtWidgets.QLabel(qwHorloge)
    self.lblFondS.setGeometry(QtCore.QRect(330, 47, 81, 55))
    font = QtGui.QFont()
    font.setFamily("DSEG14 Classic")
    font.setPointSize(36)
    font.setItalic(True)
    self.lblFondS.setFont(font)
    self.lblFondS.setStyleSheet("color: rgb(16, 32, 16);\n"
"background-color: None;")
    self.lblFondS.setTextFormat(QtCore.Qt.PlainText)
    self.lblFondS.setAlignment(QtCore.Qt.AlignCenter)
    self.lblFondS.setObjectName("lblFondS")
    self.lblS = QtWidgets.QLabel(qwHorloge)
    self.lblS.setGeometry(QtCore.QRect(330, 47, 81, 55))
    font = QtGui.QFont()
    font.setFamily("DSEG14 Classic Mini")
    font.setPointSize(36)
    font.setItalic(True)
    self.lblS.setFont(font)
    self.lblS.setStyleSheet("color: rgb(127, 255, 127);\n"
"background-color: None;")
    self.lblS.setTextFormat(QtCore.Qt.PlainText)
    self.lblS.setAlignment(QtCore.Qt.AlignCenter)
    self.lblS.setObjectName("lblS")

    self.retranslateUi(qwHorloge)
    QtCore.QMetaObject.connectSlotsByName(qwHorloge)

  def retranslateUi(self, qwHorloge):
    _translate = QtCore.QCoreApplication.translate
    self.lblFondHM.setText(_translate("qwHorloge", "~~:~~"))
    self.lblHM.setText(_translate("qwHorloge", "23:59"))
    self.lblFondS.setText(_translate("qwHorloge", "~~"))
    self.lblS.setText(_translate("qwHorloge", "59"))
