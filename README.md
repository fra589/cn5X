# cn5X++

<p align="center">
  <img src="https://github.com/fra589/cn5X/blob/master/images/XYZAB.svg" alt="5X++ Logo" />
</p>  

-------------

Nouveau panneau de contrôle Grbl 5/6 axes avec pour but d'implémenter toutes les fonctionalités de grbl-Mega-5X...  
*New 5/6 axis Grbl control panel to implement all the grbl-Mega-5X capabilities...*  
  
## Attention !  
Ce dépot est une version en cours de développement. Utilisation à vos risques et périls.
  
## *Warning !*  
*This repository is version under development. Use at your own risk.*  
  
  
| *cn5X++ is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.* |
| :--- |
  
  
## Prérequis :  
depuis la version 0.5.a, QTSerialPort à été remplacé par le module pure python pyserial qui à l'avantage de fonctionner sans (trop) de problème avec Microsoft Windows.  
cn5X++ est basé sur Python3, PyQT5 et python-serial.  
Pour installer les prérequis sur un système Linux type Debian :  
```
apt-get install python3 python3-pyqt5 python3-serial
```
En utilisation sous Linux, l'utilisateur doit faire partie du groupe Unix dialout pour pouvoir utiliser les ports série :  
```
adduser <username> dialout
```
  
## *prerequisite :*  
*since version 0.5.a, QTSerialPort has been replaced by the pure python pyserial module which has the advantage of working without (too many) problems with Microsoft Windows.*  
*cn5X ++ is based on Python3, PyQT5 and python-serial.*  
*To install the prerequisites on a Linux system such as Debian:*  
```
apt-get install python3 python3-pyqt5 python3-serial
```
*When using under Linux, the user must be part of the Unix dialout group to be able to use the serial ports:*  
```
adduser <username> dialout
```
  
-------------
cn5X++ is an open-source project and fueled by the free-time of our intrepid administrators and altruistic users. If you'd like to donate, all proceeds will be used to help fund supporting hardware and testing equipment. Thank you!  
  
[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://paypal.me/pools/c/842hNSm2It)
  
