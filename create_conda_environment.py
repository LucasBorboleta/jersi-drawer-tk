#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create the conda environment

@author: Lucas Borboleta
"""


import os
import re
import subprocess
import shutil
import sys
    

_product_home = os.path.abspath(os.path.dirname(__file__))
_env_path = os.path.join(_product_home, ".env")
_env_file = os.path.join(_product_home, "requirements.txt")

os.chdir(_product_home)

if os.path.isdir(_env_path):
    print()
    print("Removing existing environment ...")
    shutil.rmtree(_env_path)
    print("Removing existing environment done")

print()
print("Creating new environment directory ...")
os.mkdir(_env_path)
print("Creating new environment directory done")


if os.name == 'nt':
    _sys_python_path = os.path.dirname(sys.executable)
     
    if 'PATH' in os.environ:
        os.environ['PATH'] =  (_sys_python_path + os.pathsep +
                              os.path.join(_sys_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_sys_python_path, 'Library', 'bin') + os.pathsep +
                              os.environ['PATH'] )
    else:
        os.environ['PATH'] = (_sys_python_path + os.pathsep +
                              os.path.join(_sys_python_path, 'Scripts') + os.pathsep +
                              os.path.join(_sys_python_path, 'Library', 'bin') )

print()
print("Creating the environment ...")
subprocess.run(args=["conda", "create", "--prefix", _env_path, "--yes"], shell=False, check=True)
print()
print("Creating the environment done")

            
print()
print("Installing the packages ...")

package_spec_list = list()

with open(_env_file, 'r') as env_stream:
    for line in env_stream:
        if re.match(r'^\s*(#.*)?$', line):
            pass

        else:
            package_spec_list.append(line.strip())

for package_spec in package_spec_list:
    subprocess.run(args=["conda", "install", "--prefix", _env_path, "--yes", package_spec], shell=False, check=True)

print()
print("Installing the packages done")






