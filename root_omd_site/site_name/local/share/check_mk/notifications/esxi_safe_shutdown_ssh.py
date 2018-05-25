#!/bin/python
# Datamind VMWare vSphere / ESXi Safe Shutdown
# Developed by Ian Utbjoa (ian.utbjoa@gmail.com)
# Additions by Mart Verburg (mart.verburg@me.com)
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
	import sys
	import paramiko
	import argparse
	import time
	import os
	import logging
except ImportError:
	print "Required librarys for this application are:\n\tsys\n\tparamiko\n\targparse\n\ttime\n\tos\n\tlogging\n\n Make sure these are installed on your system"



def shutdown_esxi_ssh_cmd(host, username, password, port, dryrun, logger):
	"""
	Shutsdown ESXi host from remote computer over ssh
	"""
	kill_cron					= "/bin/kill $(cat /var/run/crond.pid)"
	make_remote_script_exe		= "chmod +x /tmp/shutdown.sh"
	add_cron_job				= r"""echo "$(date -D '%s' +"%M %H %d %m" -d "$(( `date +%s`+60 ))") * /tmp/shutdown.sh" >> /var/spool/cron/crontabs/root"""
	start_cron					= "crond"
	get_vm_ids_cmd 				= "vim-cmd vmsvc/getallvms"
	shutdown_guest_cmd 			= "vim-cmd vmsvc/power.shutdown " # add vm id to the end of this line
	set_maintenance_mode_cmd 	= "esxcli system maintenanceMode set -e true -t 0"
	shutdown_esxi_host_cmd		= "esxcli system shutdown poweroff -d 10 -r \"Shotdown from Nagios.\""
	exit_maintenance_mode_cmd	= "esxcli system maintenanceMode set -e false -t 0"

	try:
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		logger.info("Opening SSH session to host %s" % host)

		try:
			if not password:
				logger.info("attempting RSA key auth")
				privatekeyfile = os.path.expanduser('~/.ssh/id_rsa')
				mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
				client.connect(host, port=port, username=username, pkey=mykey)
			else:
				logger.info("attempting password auth")
				client.connect(host, port=port, username=username, password=password)
		except Exception as e:
			logger.error("Error while opening SSH session: %s" % e)
			sys.exit(1)

		# Get all defined VM's
		stdin, stdout, stderr = client.exec_command(get_vm_ids_cmd)
		output = stdout.readlines()

		# note we might filter only running VM's using
		#     vim-cmd vmsvc/power.getstate VMID
		# but this has no consequence as ESXi will not use significant time to
		# try and shutdown a powered off VM.

		vm_ids = []

		# Parse VM ID's from collumn 0 and any <shutdown_priority=XX> tags from annotation
		for line in output:
			shutdown_priority = 50    # default priority
			collumn = line.split()
			for word in collumn:
				if "<shutdown_priority=" in word:
					shutdown_priority = int(word.strip('<shutdown_priority=').strip('>'))
			if is_number(collumn[0]) == True:
				vm_ids.append((shutdown_priority, int(collumn[0])))
		if args.verbosity >= 2:
			logger.debug ("raw VM ID's and shutdown_priority registered:")
			logger.debug (vm_ids)

		# sort with ascending shutdown_priority
		vm_ids.sort(key=lambda tup: tup[0])
		if args.verbosity >= 2:
			logger.debug ("sorted VM ID's and shutdown_priority:")
			logger.debug (vm_ids)

		# create local shell script file to be uploaded
		bash_file_to_write = []
		bash_file_to_write.append("!#/bin/sh\n")
		for vm_id in vm_ids:
			if vm_id[0] > 90:
				# allow extra pause for other VM's to shutdown before the ones that must come last
				bash_file_to_write.append("sleep 240\n")
		 	bash_file_to_write.append(("%s%s\n" % (shutdown_guest_cmd, vm_id[1])))

		# Wait a number of seconds to allow VMs to shutdown safely
		bash_file_to_write.append("sleep 120\n")

		# put host in maintenance Mode as recommended before power off
		bash_file_to_write.append("%s\n" % set_maintenance_mode_cmd)
		bash_file_to_write.append("sleep 5\n")

		# start power down sequence
		bash_file_to_write.append("%s\n" % shutdown_esxi_host_cmd)

		# after a few seconds, exit maitenance mode just before power down
		# sequence completes to allow easy startup and autostart of VMs
		bash_file_to_write.append("sleep 10\n")
		bash_file_to_write.append("%s\n" % exit_maintenance_mode_cmd)

		logger.debug ("here's the prepared remote shutdown script:")
		logger.debug (bash_file_to_write)


		logger.info("Sending remote shutdown script")
		sftp = client.open_sftp()
		remote_file = sftp.file('/tmp/shutdown.sh', 'w+')
		for line in bash_file_to_write:
			remote_file.write("%s" % line)
		remote_file.flush()

		stdin, stdout, stderr = client.exec_command(make_remote_script_exe)
		stdin, stdout, stderr = client.exec_command(kill_cron)
		if not dryrun:
			logger.info("Adding shutdown script to vSphere host crontab")
			stdin, stdout, stderr = client.exec_command(add_cron_job)
		stdin, stdout, stderr = client.exec_command(start_cron)
		logger.info("Done deal")

	except Exception, e:
		logger.error("Something done gone worng! %s" % e)
	finally:
		sftp.close()
		client.close()


def is_number(s):
	"""
	Check if string/char can be converted to number
	"""
	try:
		float(s)
		return True
	except ValueError:
		pass

	try:
		import unicodedata
		unicodedata.numeric(s)
		return True
	except (TypeError, ValueError):
		pass

	return False


def cliArgs():
	"""
	Reads and parses command line arguments.
	and returns a dictionary of arguments.
	"""
	parser = argparse.ArgumentParser(description="perform safe shutdown of VMWare vSphere ESXi VMs and host over SSH. Needs VMWare Tools installed in VM\'s. Will use any <shutdown_priority=XX> tags you placed in VMs annotation.")
	parser.add_argument('-i','--host', required=True, help='IP or host name of ESXi host.')
	parser.add_argument('-u', '--username', required=False, default="root", help='ESXi host username.  Defaults to root.')
	parser.add_argument('-o','--password', required=False, help='ESXi host password. Will attempt to use ~/.ssh/id_rsa if omitted.')
	parser.add_argument('-p','--port', required=False, type=int, default=22, help='ssh port. Defaults to 22.')
	parser.add_argument('-d','--dryrun', required=False, action='store_true', help='Dryrun only, will not append uploaded script to ESXi root crontab')
	parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")

	return parser.parse_args()

class CustomAdapter(logging.LoggerAdapter):
    """
    This adapter expects the passed in dict-like object to have a
    'host' key, whose value in brackets is prepended to the log message.
	insprired by https://docs.python.org/2/howto/logging-cookbook.html#using-loggeradapters-to-impart-contextual-information
    """
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['host'], msg), kwargs


if __name__ == '__main__':
	args = cliArgs()

	# create logger with 'esxi_safe_shutdown_ssh'
	logger_base = logging.getLogger('esxi_safe_shutdown_ssh')

	logger = CustomAdapter(logger_base, {'host': args.host})

	logger_base.setLevel(logging.DEBUG)

	# create console handler with a higher log level
	ch = logging.StreamHandler()


	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	ch.setFormatter(formatter)

	# add the handlers to the logger
	logger_base.addHandler(ch)

	if (args.verbosity > 0):
		logger.info("Executing %s" % sys.argv[0])
		logger.info("Log level set to verbosity level %d" % args.verbosity)
		if args.verbosity == 1:
			ch.setLevel(logging.INFO)
		elif args.verbosity == 2:
			ch.setLevel(logging.DEBUG)

		logger.info("verbosity level set to %d" % args.verbosity)
	if (args.dryrun):
		logger.info("performing dryrun, will not start remote cronjob for shutdown script")
	shutdown_esxi_ssh_cmd(args.host, args.username, args.password, args.port, args.dryrun, logger)
