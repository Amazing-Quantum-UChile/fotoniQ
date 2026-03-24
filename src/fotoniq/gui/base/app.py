#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ----------------------------------
# Created on the Tue Mar 24 2026 by Victor
#
# Copyright (c) 2026 - AmazingQuantum@UChile
# ----------------------------------
#
'''
Content of app.py

Please document your code ;-).

'''


from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
)
from PyQt5.QtGui import QIcon
import qdarkstyle
import sys, os

class FotoniQAppBase(QMainWindow):

    def __init__(self, model, darkstyle=False):
        ## We must construct a QApplication before a QWidget
        app = QApplication(sys.argv)
        super().__init__()
        self._app = app
        self.model = model
        self.set_icon(icon="128.png")
        if darkstyle: 
            self._app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    def set_icon(self, icon="atom.png"):
        """
        Method to be used by the user to set the app icon

        Parameters
        ----------
        icon : path or string, optional
            path to the app icon. The default is "atom.png".
        """
        if os.path.exists(icon):
            self._app.setWindowIcon(QIcon(icon))
            return
        path_to_icon = os.path.join("icons", icon)
        if os.path.exists(path_to_icon):
            self._app.setWindowIcon(QIcon(path_to_icon))
            return
        path_to_icon = os.path.join(os.path.dirname(__file__), "icons", icon)
        if os.path.exists(path_to_icon):
            icon = QIcon(path_to_icon)
            self._app.setWindowIcon(icon)
            return
        logger.warning(
            f" Did not found the {icon} you required. Trying to set the default icon. "
        )

    def run(self):
        sys.exit(self._app.exec_())