#!/bin/python
# Datamind Linux hosts shutdown and halt script as Check_MK Notification plugin
# to send a shutdown -h command to the hosts you need to shutdown, like with a
# UPS triggered emergency shutdown.
# Linux hosts must have the current user's SSH public
# key in place for root user so no passwords need to be passed.
# Reads environment variable NOTIFY_PARAMETERS passed by Check_MK
# to the shutdown script as arguments
# Will read multiple hosts if Specified after -ip / --hosts separated by spaces
# Script calls are spawned as background process using nuhup to allow parallel
# processing of shutdown script for multiple hosts, output log is appended
# to notification.log file.
#
# Developed Mart Verburg (mart.verburg@me.com)
# Copyright (C) 2016  Datamind AS
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


try:
	import os
	import subprocess
except ImportError:
	print "Required librarys for this application are:\n\subprocess\n\tos\n\n Make sure these are installed on your system"


if __name__ == '__main__':
	env_parms = os.environ['NOTIFY_PARAMETERS']
	print "parameters found in environment: %s" % env_parms

	# split whitespace into parameter list of words
	parm_words = env_parms.split()

	# arguments to pass to main script
	args = []

	# fish out one or more hosts separated by whitespaces
	hosts = []
	parm_iter = iter(parm_words)
	for parm_word in parm_iter:
		try:
			if (parm_word=="-i" or parm_word=="--host"):
				#print "Found environment parameter to specify host(s): %s" % parm_word
				parm_word = parm_iter.next()
				#print "checking environment parameter word for viable host: %s" % parm_word
				while "-" not in parm_word:    # dash (-) marks next parameter
					hosts.append(parm_word)    # word after -i og --host should be an IP or hostname
					#print "Found environment parameter for following host(s): %s" % parm_word
					parm_word = parm_iter.next()      # skip to next word
			#print "Found environment parameter word: %s" % parm_word
			args.append(parm_word)
		except StopIteration:
			break

	# debug statements
	#print "Specified hosts found: %s" % hosts

	for host in hosts:
		try:
			# Get hold of logfile
			home_foldername = os.path.expanduser('~')
			notify_logfilename = home_foldername + "/var/log/notify.log"
			outfile = open(notify_logfilename, 'a+')
			errfile = open(notify_logfilename, 'a+')

			print "Linux shutdown script handling host %s" % host

			## use nohub for backgrounding child process so multiple hosts may be handled in parallel
			#exec_args = ["nohup"] + ["ssh"] + ["root@" + host] + ["echo 'testing' >> /tmp/test.log"] + args
			exec_args = ["nohup"] + ["ssh"] + ["root@" + host] + ["shutdown -h now"]
			# debug statements
			print "Executing new background subprocess:"
			print exec_args
			subprocess.Popen(exec_args, stdout=outfile,stderr=errfile)
		except Exception, e:
			print("Something done gone worng! %s" % e)
	print "Done calling Linux shutdown script"
