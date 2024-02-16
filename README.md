# cn5X++ <img src="https://github.com/fra589/cn5X/blob/master/images/XYZAB.svg" alt="5X++ Logo" width="127 px" align="right"/>

<p align="center">
  <a href="https://github.com/fra589/cn5X/tree/master/images/screenshots" title="Screenshots">
    <img src="https://github.com/fra589/cn5X/blob/master/images/screenshots/cn5X_screenShot_00.png" alt="5X++ Screenshot" width="1024 px"/>
  </a>
</p>  

Panneau de contrôle Grbl 5/6 axes avec pour but d'implémenter toutes les fonctionalités de grbl-Mega-5X...  
*5/6 axis Grbl control panel to implement all the grbl-Mega-5X capabilities...*  
  
| *cn5X++ is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.* |
| :--- |
  
  
## Prérequis :  
cn5X++ est basé sur Python3, python-serial, PyQt6, Qt6-SVG et Qt6.qtmultimedia.  
Pour installer les prérequis sur un système Linux type Debian :  
```
sudo apt install python3-pyqt6 python3-pyqt6.qtmultimedia libqt6multimedia6 libqt6svg6 pyqt6-dev-tools
```
En utilisation sous Linux, l'utilisateur doit faire partie du groupe Unix dialout pour pouvoir utiliser les ports série :  
```
sudo adduser <username> dialout
```

Après avoir installé les prérequis, copiez l'ensemble du dépôt cn5X++ (avec tous ses sous-répertoires) sur votre ordinateur puis, "exécutez" le script principal "`cn5x.py`"

## *prerequisite :*  
*cn5X ++ is based on Python3, python-serial, PyQt6, Qt6-SVG et Qt6.qtmultimedia.*  
*To install the prerequisites on a Linux system such as Debian:*  
```
sudo apt install python3-pyqt6 python3-pyqt6.qtmultimedia libqt6multimedia6 libqt6svg6 pyqt6-dev-tools
```
*When using under Linux, the user must be part of the Unix dialout group to be able to use the serial ports:*  
```
sudo adduser <username> dialout
```
  
After installing the prerequisites, copy the entire cn5X++ repository (with all its subdirectories) to your computer and then "run" the main script "`cn5x.py`"

-------------
cn5X++ is an open-source project and fueled by the free-time of our intrepid administrators and altruistic users. If you'd like to donate, all proceeds will be used to help fund supporting hardware and testing equipment. Thank you! [![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate/?business=CZZN52UPPVHCW&no_recurring=0&item_name=Grbl-Mega-5X+%26+cn5X%2B%2B+donations&currency_code=EUR)
