#!/usr/bin/python3

"""
Holds classes that do not fall into other categories used by other parts of the program.
Requires:
    Python3.4 or Python2.7(some issues)
    PIL - Python Imaging Library
    feh
    pexpect
Written by Dwane Gard
"""

from __future__ import print_function, division, absolute_import
from builtins import *
from PIL import Image, ImageFont, ImageDraw
import io
import subprocess
import os
import sys
from threading import *
import threading
import signal


from ExternalConnection import CiscoConnections, LinuxConnection
import ReadConfig


def read_config():
    global cisco_devices, server_devices
    global width
    global height
    global good_colour
    global intermediate_colour
    global bad_colour

    cisco_devices = []
    server_devices = []

    # rules = [good_colour.__name__, intermediate_colour.__name__, bad_colour.__name__
    #          width.__name__, height.__name__,]
    rules = ['good_colour', 'intermediate_colour', 'bad_colour', 'width', 'height',
             'cisco_device{password,user,host}', 'server_device{password,user,host,port}']

    readConfig = ReadConfig.ReadConfig(rules, debug_flag=debug_flag, conf_file_name='conf')
    single_line_rules, multi_line_rules = readConfig.output()

    for each_setting in single_line_rules:
        if each_setting.rule == 'width':
            width = int(each_setting.conf)
        elif each_setting.rule == 'height':
            height = int(each_setting.conf)
        elif each_setting.rule == 'good_colour':
            good_colour = each_setting.conf
        elif each_setting.rule == 'intermediate_colour':
            intermediate_colour = each_setting.conf

    for each_setting in multi_line_rules:
        working_host = None
        working_password = None
        working_user = None

        if each_setting.rule == 'server_device':
            for each_subRule in each_setting.subRules:
                if each_subRule.rule == 'password':
                    working_password = each_subRule.conf
                elif each_subRule.rule == 'user':
                    working_user = each_subRule.conf
                elif each_subRule.rule == 'host':
                    working_host = each_subRule.conf
                elif each_subRule.rule == 'port':
                    working_port = each_subRule.conf
            server_devices.append(ServerDevices(each_setting.rule_label, working_user, working_password, working_host, working_port))

        elif each_setting.rule == 'cisco_device':
            for each_subRule in each_setting.subRules:
                if each_subRule.rule == 'password':
                    working_password = each_subRule.conf
                elif each_subRule.rule == 'user':
                    working_user = each_subRule.conf
                elif each_subRule.rule == 'host':
                    working_host = each_subRule.conf
            cisco_devices.append(CiscoDevices(each_setting.rule_label, working_user, working_password, working_host))
    return width, height, good_colour, intermediate_colour, bad_colour, cisco_devices, server_devices


# Store credentials for the cisco devices
class CiscoDevices:
    def __init__(self, name, user, password, host):
        self.user = user
        self.ip = host
        self.passwd = password
        self.name = name

    def output(self):
        return self.ip, self.user, self.passwd


# For storing server information
class ServerDevices:
    def __init__(self, name, user, password, host, port):
        self.ip = host
        self.user = user
        self.port = port
        self.passwd = password

        self.name = name

    # Return a standard output
    def output(self):
        return self.ip, self.user, self.passwd


# Set exit flag to exit checked when the time is right to exit gracefully
def signal_handler(signal, frame):
    global exit_flag

    print('[!!!] Exiting gracefully')
    exit_flag = True

# Manages server connection threads
def server_con(q, local_server_output):
    while True:
        if q.empty() is True:
            break
        ze_args = (q.get())
        ze_args = ze_args.split("|")
        local_server_output.append(LinuxConnection(ze_args[0], ze_args[1], ze_args[2], ze_args[3]))
        q.task_done()


# Manages end point connection threads
def end_point_con(q, local_ssh_connections):
    while True:
        if q.empty() is True:
            break
        ze_args = (q.get())
        ze_args = ze_args.split("|")
        ssh = (CiscoConnections(ze_args[0], ze_args[1], ze_args[2]))
        local_ssh_connections.append(ssh)
        q.task_done()


def runserver_threaded_connections(server_q, end_point_q, debug_flag):
    global cisco_connections
    global server_output

    max_threads = 4     # per worker

    # This should always be one with current config
    if debug_flag == 1:
        print("[Threads active][%s]" % threading.active_count())
    # if threading.active_count() == 1:
    if debug_flag == 1:
        print('[Running connections]')
        print('[-] clearing old ssh server')

    # Clear out old data as to not have an infinitely expanding list
    server_output = []

    # Define the args to connect to each server and put them in queue
    for each_server in server_devices:
        server_args = "%s|%s|%s|%s" % (each_server.ip, each_server.user, each_server.passwd, each_server.port)
        server_q.put(server_args)

    # Send the queue to the worker function
    for each in range(max_threads):
        server_worker = Thread(target=server_con, args=(server_q, server_output))
        server_worker.setDaemon(True)
        server_worker.start()
    if debug_flag == 1:
        print('[-] clearing old ssh connections')

    # Clear out old data as to not have an infinitely expanding list
    cisco_connections = []

    # Define the args to connect to each cisco device and put them in a queue
    for each_ssh in cisco_devices:
        ssh_args = "%s|%s|%s" % (each_ssh.ip, each_ssh.user, each_ssh.passwd)
        end_point_q.put(ssh_args)

    # Send the queue to the worker function
    for each in range(max_threads):
        ssh_worker = Thread(target=end_point_con, args=(end_point_q, cisco_connections))
        ssh_worker.setDaemon(True)
        ssh_worker.start()

    # Block progression of the script till all queues are empty
    server_q.join()
    end_point_q.join()
    if debug_flag == 1:
        print('[Finished Connections]')
    return server_output, cisco_connections


if __name__ == '__main__':
    print('[!] Use "system_health.py" to run the program')
