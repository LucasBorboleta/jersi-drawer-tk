#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Launch the JERSI GUI in the correct environment

@author: Lucas Borboleta
"""

_COPYRIGHT_AND_LICENSE = """
JERSI-DRAWER-TK draws a vectorial picture of JERSI boardgame state from an abstract state.

Copyright (C) 2020 Lucas Borboleta (lucas.borboleta@free.fr).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses>.
"""

import os
import subprocess  

_product_home = os.path.abspath(os.path.dirname(__file__))
_jersi_gui_executable = os.path.join(_product_home, "jersi_drawer_tk", "jersi_gui.py")
_venv_home = os.path.join(_product_home, ".env")

os.chdir(_product_home)

print()
print("Determining the python executable ...")

if os.name == 'nt':
    
    _venv_python_executable = os.path.join(_venv_home, "python.exe")

    _venv_python_path = os.path.dirname(_venv_python_executable)
     
    if 'PATH' in os.environ:
        os.environ['PATH'] =  (_venv_python_path + os.pathsep +
                              os.path.join(_venv_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_venv_python_path, 'Library', 'bin') + os.pathsep +
                              os.environ['PATH'] )
    else:
        os.environ['PATH'] = (_venv_python_path + os.pathsep +
                              os.path.join(_venv_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_venv_python_path, 'Library', 'bin') )

else:
    ##TODO: define setup for Linux
    assert os.name == 'nt'
    
print("    _venv_python_executable = ", _venv_python_executable)
print("Determining the python executable done")


print()
print("jersi_gui ...")
print()
print(_COPYRIGHT_AND_LICENSE)
subprocess.run(args=[_venv_python_executable, _jersi_gui_executable], shell=False, check=True)
print()
print("jersi_gui done")



