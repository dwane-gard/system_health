#!/usr/bin/python3

"""
Simple script that creates and applies a background with system information data.
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
from DrawImage import DrawImage, ShapeAlerts

# Global variables
cisco_devices = []
server_devices = []
server_output = []
cisco_connections = []

# Raised for graceful exit
exit_flag = False
debug_flag = 0

# In case not defined in config
good_colour = '#00AA00'
intermediate_colour = '#FFA500'
bad_colour = '#FF0000'


# Read the config file or create one if it does not exist
def read_config():
    global cisco_devices, server_devices
    global width
    global height
    global good_colour
    global intermediate_colour
    global bad_colour

    device = ''
    device_settings = []
    cisco_devices = []
    server_devices = []

    # Check if conf file exist, if not create it
    if not os.path.exists('conf'):
        open('conf', 'w').write('# Configuration file for dynamic_background_generator\n'
                                '# Written by Dwane Gard\n\n'
                                'cisco_device=\t{\n'
                                '\tpassword=\n'
                                '\tuser=\n'
                                '\thost=\n'
                                '\tport=\n'
                                '}\n'
                                'server-device=\t{\n'
                                '\tpassword=\n'
                                '\tuser=\n'
                                '\thost=\n'
                                '\tport=\n'
                                '}\n'
                                'height=\n'
                                'width=\n'
                                'good_colour=#00AA00\n'
                                'intermediate_colour=#FFA500\n'
                                'bad_colour=#FF0000\n')

    # Open and read the conf file
    with open('conf', 'r') as configuration:
        configuration = configuration.read()
        configuration_as_list = configuration.split("\n")

        cisco_config_open = False
        server_config_open = False
        for each_line in configuration_as_list:
            if each_line.startswith('#'):
                continue
            # Find each cisco or server device and record each line as a setting
            if each_line.startswith('cisco_device='):
                cisco_config_open = True
                device = (each_line.split('=')[1])
                try:
                    device = device.split('}')[0]
                except:
                    pass

            if each_line.startswith('server_device='):
                server_config_open = True
                device = (each_line.split('=')[1])
                try:
                    device = device.split('}')[0]
                except:
                    pass

            device_settings.append(each_line)

            if debug_flag == 1:
                print('[device] %s' % device)
                print('[device_settings] %s' % device_settings)

            # When the '}' is found package the settings and add them to the list of devices
            if '}' in each_line:
                if debug_flag == 1:
                    if server_config_open:
                        print('Ending Server %s' % device)
                    if cisco_config_open:
                        print('[+] Finalizing cisco device %s' % device)
                if cisco_config_open is True:
                    cisco_devices.append(CiscoDevices(device, device_settings))
                    cisco_config_open = False
                    del device_settings[:]
                    # device_settings.clear()

                elif server_config_open is True:
                    server_devices.append(ServerDevices(device, device_settings))
                    server_config_open = False
                    del device_settings[:]
                    # device_settings.clear()

            # Find the other settings and apply them where necessary
            elif each_line.startswith('height='):
                height = each_line.split('=')[1]
                height = int(height)
            elif each_line.startswith('width='):
                width = each_line.split('=')[1]
                width = int(width)
            elif each_line.startswith('good_colour='):
                good_colour = each_line.split('=')[1]
            elif each_line.startswith('intermediate_colour='):
                intermediate_colour = each_line.split('=')[1]
            elif each_line.startswith('bad_colour='):
                bad_colour = each_line.split('=')[1]

        if device == '':
            print('[!] Configuration File not configured!\n'
                  'Creating File "conf" in script directory.\n'
                  'Populate with:\n'
                  'cisco_device=\t{\n'
                  '\tpassword=\n'
                  '\tuser=\n'
                  '\thost=\n'
                  '}\n'
                  'server-device=\t{\n'
                  '\tpassword=\n'
                  '\tuser=\n'
                  '\thost=\n'
                  '\tport=\n'
                  '}\n'
                  'height=\n'
                  'width=\n'
                  'good_colour=#00AA00\n'
                  'intermediate_colour=#FFA500\n'
                  'bad_colour=#FF0000\n')
            sys.exit()
    if debug_flag == 1:
        print('[cisco_settings] %s' % cisco_devices)
        print('[server_devices] %s' % server_devices)




# Store credentials for the cisco devices
class CiscoDevices:
    def __init__(self, name, settings):
        for each_setting in settings:
            if 'user' in each_setting:
                self.user = each_setting.strip()
                self.user = self.user.split('=')[1]
            if 'password' in each_setting:
                self.passwd = each_setting.strip()
                self.passwd = self.passwd.split('=')[1]
            if 'host' in each_setting:
                self.ip = each_setting.strip()
                self.ip = self.ip.split('=')[1]

        self.name = name

    def output(self):
        return self.ip, self.user, self.passwd


# For storing server information
class ServerDevices:
    def __init__(self, name, settings):
        for each_setting in settings:
            if 'user' in each_setting:
                self.user = each_setting.strip()
                self.user = self.user.split('=')[1]
            if 'password' in each_setting:
                self.passwd = each_setting.strip()
                self.passwd = self.passwd.split('=')[1]
            if 'host' in each_setting:
                self.ip = each_setting.strip()
                self.ip = self.ip.split('=')[1]
            if 'port' in each_setting:
                self.port = each_setting.strip()
                self.port = self.port.split('=')[1]

        self.name = name

    # Return a standard output
    def output(self):
        return self.ip, self.user, self.passwd


# Set exit flag to exit checked when the time is right to exit gracefully
def signal_handler(signal, frame):
    global exit_flag

    print('[!!!] Exiting gracefully')
    exit_flag = True



# Add a count on how manny loops the script has run on the bottom of the screen
def add_count(draw, count):
    draw.text((width/2, height-80), str(count), font=font, fill='#00AA00')


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


def runserver_threaded_connections(server_q, end_point_q):
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
    # else:
    #     if debug_flag == 1:
    #         print('[!!] Thread is flailing, attempting to recover')
    #     threading._shutdown()


# Variable Settings and some initialization
width, height = 1920, 1080  # Default setting
try:
    read_config()
except ValueError:
    print('[!] Configuration is unreadable. Review configuration file: conf in program directory and ensure the data is correct.')
font = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 26)
font_small = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 20)


shape_origin = (width * .8, height * .91)

# Send captured SIGINT's to signal handler function to allow for a graceful exit
signal.signal(signal.SIGINT, signal_handler)
shapes_to_draw_class = [ShapeAlerts(shape_origin, 0, ""), ]


def main():
    count = 0

    createImage = DrawImage(count)
    createImage.reset_data()
    createImage.get_font_size()

    while True:
        # Check if user wants to exit before any connections are opened
        if exit_flag is True:
            exit(0)

        count += 1

        createImage.reset_data()
        img = createImage.return_image()

        # Output to io stream
        ze_output = io.BytesIO()
        img.save(ze_output, format='PNG')
        contents = ze_output.getvalue()

        # Set as background
        proc = subprocess.Popen(['feh', '--bg-scale', '-'], stdin=subprocess.PIPE)
        proc.communicate(contents)

        ze_output.close()


if __name__ == '__main__':
    main()
