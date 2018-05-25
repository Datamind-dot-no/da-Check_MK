#!/bin/python
# Datamind Stupid windows shutdown
# Developed by Ian Utbjoa (ian.utbjoa@gmail.com)
# Copyright (C) 2017  Datamind AS
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import subprocess
import argparse

# Global var's
USER_NAME = "safes"
PASSWORD = "ANSIKT-1917-Antenne"

def cliArgs():
    """
	Reads and parses command line arguments.
	and returns a dictionary of arguments.
	"""
    parser = argparse.ArgumentParser(description="Shutsdown or restarts Windows physical machines from Linux. Requiers the \"net rpc\" command.")
    parser.add_argument('-i','--host', required=True, action='append', help='IP or host name of Windows host.')
    parser.add_argument('-r', '--restart', required=False, default=False, help='Set this flag to restart the hosts')

    return parser.parse_args()

if __name__ == '__main__':
    args = cliArgs()

    if args.restart == False:
        for host in args.host:
            exec_args = ["net", "rpc", "shutdown", "-f", "-t" "0", "-C", "'check_mk'", "-U", USER_NAME + "%" + PASSWORD, "-I", args.host]
            subprocess.Popen(exec_args, stdout=None,stderr=None)
    else:
        for host in args.host:
            exec_args = ["net", "rpc", "shutdown", "-r", "-t" "0", "-C", "'check_mk'", "-U", USER_NAME + "%" + PASSWORD, "-I", args.host]
            subprocess.Popen(exec_args, stdout=None,stderr=None)
