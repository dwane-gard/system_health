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
import time
import io
import socket
import subprocess
import pexpect
import os
import sys
import math
from pexpect import pxssh
from threading import *
from queue import Queue
import threading
import signal

# Global variables
cisco_devices = []
server_devices = []
server_output = []
cisco_connections = []

# Raised for graceful exit
exit_flag = False
debug_flag = 0


# Read the config file or create one if it does not exist
def read_config():
    global cisco_devices
    global width
    global height
    global good_colour
    global intermediate_colour
    global bad_colour

    device = ''
    device_settings = []

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
        # line_count = 0       # Think this is obscelete

        cisco_config_open = False
        server_config_open = False
        for each_line in configuration_as_list:
            # line_count += 1       # Think this is obscelete

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

            # When the '}' is found package the settings and add them to the list of devices
            if '}' in each_line:
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


# holds information to draw hexagon pattern that indicates recent error history
class ShapeAlerts:
    def __init__(self, origin, error_case, error_message):
        self.origin = origin
        self.error_case = error_case
        self.error_message = error_message


# Gets DSL info from cisco 877 or 887
class SSH:
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.ze_output = ""
        self.status_colour = good_colour
        if debug_flag == 1:
            print('[User@Host] %s@%s' % (self.user, self.host))
        try:
            self.ssh = self.connect()

            self.version = self.check_version(self.ssh)
            self.status, self.download, self.upload, self.crc = self.check_dsl(self.ssh, self.version)
            self.output()
            self.close_connection(self.ssh)

        except:
            self.status, self.download, self.upload, self.crc = "Dead", '0', '0', '0'
            self.status_colour = bad_colour
            self.output()

    # unused
    def get_status_color(self):
        status_colour = bad_colour
        return status_colour

    def output(self):
        self.status = ('[%s] ' % self.host) + self.status

        self.download = self.download.strip()
        self.download = '[DL] ' + self.download

        self.upload = self.upload.strip()
        self.upload = '[UL] ' + self.upload

        self.crc = self.crc.strip()
        self.crc = '[Errors] ' + self.crc

        self.ze_output = " | ".join([self.status, self.download, self.upload, self.crc])
        if debug_flag == 1:
            print('[ze_output] ' + self.ze_output)

    # Connects to ssh server and returns the connection
    def connect(self):
        host = self.host
        user = self.user
        passwd = self.passwd
        ssh_newkey = 'Are you sure you want to continue connecting (yes/no)?'
        constr = 'ssh -o KexALgorithms=diffie-hellman-group14-sha1 ' + user + '@' + host
        ssh = pexpect.spawn(constr, timeout=10)
        ssh.expect([pexpect.TIMEOUT, ssh_newkey, 'Password: '])
        ssh.sendline(passwd)
        ssh.expect(['P|password:', '>', '#'])
        return ssh

    # check the version of a cisco router
    def check_version(self, ssh):
        ssh.sendline('terminal length 0')
        ssh.sendline('show version')

        while True:
            version_output = ssh.readline()
            version_output = version_output.decode('UTF-8')

            if version_output.startswith('Cisco IOS Software, C870'):
                version = 'c870'
                return version
            elif version_output.startswith('Cisco IOS Software, C880 Software'):
                version = 'c880'
                return version
        # need to add code hear to catch if the version is incompatible with the script

    # Get information from c870 or c880 platform routers
    def check_dsl(self, ssh, version):
        dsl_output = ['Status', 'Download', 'Upload', 'CRC Errors']
        ssh.sendline('terminal length 0')

        if version is 'c870':
            ssh.sendline('show dsl int atm 0')
        elif version is 'c880':
            ssh.sendline('show controller vdsl 0')
        else:
            self.status_colour = bad_colour
            return "No Connection", '0', '0', '0'

        # Read each line until known unnecessary data is printed
        while True:
            output = ssh.readline()
            each_line = output.decode('UTF-8')

            if each_line.startswith("Modem Status:"):
                # print(each_line.encode())
                dsl_output[0] = (each_line.strip()).split('\t', 1)[1]
                if 'Showtime' in dsl_output[0]:
                    dsl_output[0] = 'Showtime!'
            if each_line.startswith("Speed (kbps):"):
                dsl_output[1] = (each_line.strip()).split('\t')[2]
                dsl_output[2] = (each_line.strip()).split('\t')[4]
            if each_line.startswith("CRC"):
                # print(each_line)
                dsl_output[3] = (each_line.strip()).split('\t')[2]
            elif each_line.startswith("Training Log"):
                break
            elif each_line.startswith('LOM Monitoring '):
                break
        ssh.sendline('exit')
        return dsl_output

    def close_connection(self, connection):
        connection.sendline('exit')
        connection.close()


# Class for connection to servers
class SystemLog:
    def __init__(self, host, user, passwd, port):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        self.users = []
        try:
            self.ssh = self.connection()

        except:
            return

        # self.get_auth(self.ssh)
        if self.ssh:
            self.get_current_users(self.ssh)

            self.close_connection(self.ssh)

    class User:
        def __init__(self, user_name, pty, date, ze_time, ip):
            self.user_name = user_name.decode('utf-8')
            self.pty = pty.decode('utf-8')
            self.ze_time = ze_time.decode('utf-8')
            self.date = date.decode('utf-8')
            self.ip = ip.decode('utf-8')

    def connection(self):
        s = pxssh.pxssh()
        s.login(self.host, self.user, self.passwd, port=self.port, login_timeout=10)
        return s

    # check who last accesed server (prety useless think it will always be this script as it reconnects constantly)
    def get_auth(self, connection):
        connection.sendline('cat /var/log/lastlog')
        connection.prompt()
        last_connection_ip = connection.before
        ze_derp = last_connection_ip
        if debug_flag == 1:
            print(ze_derp)

    # Get a list of user put info into class that hold user information and that into a list of classes
    def get_current_users(self, connection):
        connection.sendline('who')
        connection.prompt()
        output = (connection.before).split(b'\r\n')
        output.remove(b'who')
        output.remove(b'')

        for each_output in output:
            ze_split = (each_output.split(b' '))
            user_name, pty, date, ze_time, ip = [x for x in ze_split if x != b'']
            self.users.append(self.User(user_name, pty, date, ze_time, ip))

    # Future !! Get log of last update done on server
    def get_apt(self, connection):
        return

    # Future !! Get log of last back
    def rsync(self, connection):
        return

    def close_connection(self, connection):
        connection.sendline('exit')
        connection.close()


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


# Remove the first object of list it has more then 'ze_limit' items, shuffling items to the front
def list_limit(ze_list, ze_limit):
    ze_revised_list = []

    if len(ze_list) == ze_limit:
        for each_item in ze_list:
            if each_item is not ze_list[0]:
                ze_revised_list.append(each_item)
        return ze_revised_list
    else:
        return ze_list


# Get position the next shape will be drawn at depending on where the input origin is
def get_shape_origins(origin):
    start_pos_x, start_pos_y = origin

    # If shape is at the top of screen (1080) start it again at the bottom position
    if start_pos_y < 120:
        start_pos_y = 982.8

    shape_radius = 100
    shape_cut = shape_radius * math.cos(math.radians(30))
    shape_side_len = (shape_radius * math.sin(math.radians(30)))*2

    # Discover if the next shape goes to the left or to the right of the last shape
    test_number = round(int(shape_origin[1]-start_pos_y)/87, 0)
    if abs(test_number == 1) or abs(test_number == 3) or abs(test_number == 5) or abs(test_number == 7) or abs(test_number == 9):
        derp = 0
    elif abs(test_number == 0) or abs(test_number == 4) or abs(test_number == 8) or abs(test_number == 12):
        derp = -150
    else:
        derp = 150

    # Define the next shapes origin
    next_shape = (shape_origin[0] + derp,
                  (start_pos_y - shape_cut))

    return next_shape


def draw_hexagon(draw, error_case, error_msg, origin):
    start_pos_x, start_pos_y = origin
    shape_radius = 100
    shape_side_len = shape_radius * math.sin(math.radians(30))
    shape_cut = shape_radius * math.cos(math.radians(30))

    if error_case is 0:
        shape_colour = good_colour
    elif error_case is 1:
        shape_colour = intermediate_colour
    elif error_case is 2:
        shape_colour = bad_colour
    else:
        shape_colour = error_case

    # Find the lines of the hexagon depending on the start position and the sides length
    lines = []
    i = 0
    while i < 6:
        i += 1
        lines.append((start_pos_x + shape_radius * math.cos(2 * math.pi * i / 6), start_pos_y + shape_radius * math.sin(2 * math.pi * i / 6)))

    draw.polygon(lines, outline=shape_colour, fill='#000000')


class DeviceData:
    def __init__(self):
        self.dirs = self.get_dir_ls()

        # If a hwmon device is a gpu or a cpu add it to the list
        self.devices = [self.EachDevice(each_dir) for each_dir in self.dirs
                        if self.EachDevice(each_dir).device_type == 'GPU' or 'CPU']

    def get_dir_ls(self):
        # Get a list of all the dirs in hwmon
        proc = subprocess.check_output(['ls', '/sys/class/hwmon']).rstrip()
        output = proc.split(b'\n')
        return output

    class EachDevice:
        def __init__(self, ze_dir):
            if debug_flag == 1:
                print('[+] Intilizing device')
            self.ze_dir = ze_dir
            try:
                self.vendor_id, self.device_id = self.identify_dir(ze_dir)
            except:
                self.device_type = b'Unknown'
                if debug_flag == 1:
                    print('[!] Device cannot be identified, passing')
                return
            self.vendor_name, self.device_name = self.search_vendor_list(self.vendor_id, self.device_id)

            self.device_type = b'Unknown'
            self.check_if_gpu(self.device_id.split('x')[1].encode('utf-8'))
            self.check_if_cpu(self.device_id.split('x')[1].encode('utf-8'))

            self.temp_input = 0
            self.temp = ''
            self.device_status = ''

            # Get the consumer facing name of the cpu
            if self.device_type == 'CPU':
                self.device_name = self.get_real_cpu_name()

        def get_device_status(self):
            try:
                with open('/sys/class/hwmon/%s/temp1_crit' % self.ze_dir) as temp_crit:
                    temp_crit = temp_crit.read()
            except:
                temp_crit = ''
            try:
                with open('/sys/class/hwmon/%s/temp1_max' % self.ze_dir) as temp_max:
                    temp_max = temp_max.read()
            except:
                temp_max = 97000

            if self.device_type == 'GPU':
                good_temp = 45000
                int_temp = 55000
                bad_temp = temp_max

            elif self.device_type == 'CPU':

                good_temp = 35000
                int_temp = 40000
                bad_temp = temp_max

            else:
                good_temp = 35000
                int_temp = 50000
                bad_temp = 97000

            if self.temp_input < int_temp:
                self.device_status = good_colour

            elif bad_temp > self.temp_input > int_temp:
                self.device_status = intermediate_colour

            elif self.temp_input > bad_temp:
                self.device_status = bad_colour
            else:
                self.device_status = ""

        def check_if_gpu(self, device_id):
            proc1 = subprocess.Popen(['lspci', '-mm', '-nn'], stdout=subprocess.PIPE)
            proc2 = subprocess.check_output(['grep', 'VGA'], stdin=proc1.stdout)
            outputs = proc2.split(b'\n')
            outputs = [output for output in outputs if output is not b'']

            for each_output in outputs:
                if device_id in each_output.split(b'" "')[2]:
                    self.device_type = 'GPU'
                    return True
            return False

        def check_if_cpu(self, device_id):
            proc1 = subprocess.Popen(['lspci', '-mm', '-nn'], stdout=subprocess.PIPE)
            proc2 = subprocess.check_output(['grep', 'Host'], stdin=proc1.stdout)
            outputs = proc2.split(b'\n')
            outputs = [output for output in outputs if output is not b'']
            for each_output in outputs:

                if device_id in each_output.split(b'" "')[2]:
                    self.device_type = 'CPU'
                    return True
            return False

        def get_real_cpu_name(self):
            proc = subprocess.check_output((['grep', 'model name', '/proc/cpuinfo']))
            output = proc.strip()
            output = output.split(b'\n')[0]
            output = output.split(b'\t:')[1].strip()
            output = output.decode('utf-8')
            return output

        def search_vendor_list(self, vendor_id, device_id):
            vendor_id = vendor_id.split('x')[1]
            device_id = device_id.split('x')[1]
            vendor = 'Unknown Vendor'
            device = 'Unknown Device'

            try:
                # Run a process to search a local pci database
                proc1 = subprocess.check_output(['grep', vendor_id, '/usr/share/hwdata/pci.ids'])

                # Change to list with a item per line
                vendor_output = proc1.split(b'\n')

                # Check each line for the corporation name, the line will start with the vendor id
                for each_line in vendor_output:
                    if each_line.startswith(vendor_id.encode('utf-8')):
                        vendor = each_line.decode('utf-8')

                # Remove white space
                vendor = vendor.split(vendor_id)[1].lstrip()
            except subprocess.CalledProcessError as e:
                if debug_flag == 1:
                    print(e)
                pass
            except IndexError as e:
                if debug_flag == 1:
                    print(e)
                pass

            try:
                # Run a process to search a local pci database
                proc2 = subprocess.check_output(['grep', device_id, '/usr/share/hwdata/pci.ids'])

                # Re-encode and remove whitespace
                device = proc2.decode('utf-8')
                device = device.split(device_id)[1].strip()

            except subprocess.CalledProcessError as e:
                pass
            except IndexError as e:
                pass

            return vendor, device

        def identify_dir(self, ze_dir):
            # try:
            ze_dir = ze_dir.decode('utf-8')
            with open('/sys/class/hwmon/%s/device/vendor' % ze_dir) as vendor_id:
                with open('/sys/class/hwmon/%s/device/device' % ze_dir) as device_id:
                    device_id = device_id.read().strip()
                    vendor_id = vendor_id.read().strip()
            return vendor_id, device_id
            # except FileNotFoundError:
            #     ''' Need Some error fix here if the class is not an actual device '''
            #     print('[!] This device is unkown')

        def cat_temp(self):
            ze_dir = self.ze_dir.decode('utf-8')
            try:
                with open('/sys/class/hwmon/%s/temp1_input' % ze_dir) as hardware_temp:
                    temp_input = hardware_temp.read()
                    temp_input = int(temp_input)
                    temp = int(temp_input)/1000
                    self.temp_input = temp_input
                    self.temp = str(temp)
            except:
                if debug_flag == 1:
                    print('[!] Cannot Read Temp of device %s' % ze_dir)
                self.temp_input = 0
                self.temp = '0'


class CreateImage:
    def __init__(self, count):
        self.deviceData = DeviceData()

        self.image = Image.new('RGB', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        # self.count = 0

        self.ze_time = None
        self.ip_address = None
        self.gpu = None
        self.cpu = None

        self.cpu_size = None
        self.gpu_size = None
        self.int_pos = self.draw.textsize(' | ', font=font)[0]
        self.ze_time_size = None
        self.ip_address_size = None

        self.cpu_start = None
        self.gpu_start = None
        self.ip_address_start = None
        self.ze_time_start = None

        self.first_line_tot_pos = None
        self.dsl_start = []

    def return_image(self):
        self.image = Image.new('RGB', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        self.shape_pattern()
        self.write_system_health()
        self.write_endpoint_health()
        self.write_server_health()
        return self.image

    def reset_system_health(self):
        # Get system health from local system
        for each_device in self.deviceData.devices:
            each_device.cat_temp()
            each_device.get_device_status()
            if each_device.device_type == 'CPU':
                self.cpu = each_device
            if each_device.device_type == 'GPU':
                self.gpu = each_device

    def reset_data(self):
        server_q = Queue(maxsize=2)
        end_point_q = Queue(maxsize=2)

        # Get system health from local system
        for each_device in self.deviceData.devices:
            each_device.cat_temp()
            each_device.get_device_status()
            if each_device.device_type == 'CPU':
                self.cpu = each_device
            if each_device.device_type == 'GPU':
                self.gpu = each_device

        # Get server and endpoint data from remote systems
        runserver_threaded_connections(server_q, end_point_q)

        self.get_ip_address()
        self.get_time()
        self.get_font_size()

    def get_time(self):
        while True:
            # Get time
            localtime = time.asctime(time.localtime(time.time()))

            # Check if time ends in 5 or 0 sec
            if localtime[-6] == "0":
                self.ze_time = str('[Time] ' + localtime)
                return str('[Time] ' + localtime)

            elif localtime[-6] == "5":
                self.ze_time = str('[Time] ' + localtime)
                return str('[Time] ' + localtime)

            else:
                # Sleep till the time is right
                if int(localtime[-6]) < 5:
                    time.sleep(5-int(localtime[-6]))
                else:
                    time.sleep(10-int(localtime[-6]))

    def get_ip_address(self):
        try:
            ip_addr = socket.gethostbyaddr(socket.getfqdn())

            if ip_addr[2][0] == '127.0.1.1' or ip_addr[1][0] == 'localhost':
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('google.com', 0))
                ip_addr = s.getsockname()[0]
            self.ip_address = str('[IP] ' + ip_addr), good_colour
            return str('[IP] ' + ip_addr)

        except:
            self.ip_address = "[IP] No Connection", intermediate_colour

    def get_font_size(self):
        self.cpu_size = self.draw.textsize(self.cpu.temp, font)[0]
        self.gpu_size = self.draw.textsize(self.gpu.temp, font)[0]

        self.ip_address_size = self.draw.textsize(self.ip_address[0], font)[0]
        self.ze_time_size = self.draw.textsize(self.ze_time, font)[0]

        self.first_line_tot_pos = self.cpu_size + self.int_pos + self.gpu_size\
                                  + self.int_pos + self.ze_time_size + self.int_pos\
                                  + self.ip_address_size + self.int_pos

        for each_connection in cisco_connections:
            next_line = self.draw.textsize(each_connection.ze_output, font)[0]
            self.dsl_start.append((width - next_line) / 2)

        # Find the position to start writing depending on declared resolution
        start_pos = (width - self.first_line_tot_pos) / 2
        self.cpu_start = start_pos
        self.gpu_start = self.cpu_start + (self.draw.textsize(self.cpu.temp, font))[0] + self.int_pos
        self.ze_time_start = self.gpu_start + (self.draw.textsize(self.gpu.temp, font))[0] + self.int_pos
        self.ip_address_start = self.ze_time_start + (self.draw.textsize(self.ze_time, font))[0] + self.int_pos
        return

    def shape_pattern(self):
        global shapes_to_draw_class

        # Draw the shapes
        for each_shape in shapes_to_draw_class:
            draw_hexagon(self.draw, each_shape.error_case, each_shape.error_message, each_shape.origin)

        # Set next loop to default error state
        next_shape_colour = good_colour

        # Check if next loop should have an error state
        try:
            for each_device in self.deviceData.devices:
                if each_device.device_status == intermediate_colour:
                    next_shape_colour = intermediate_colour
                    break
                elif each_device.device_status == bad_colour:
                    next_shape_colour = bad_colour
                    break
            for each_connection in cisco_connections:
                if next_shape_colour == good_colour and next_shape_colour != bad_colour:
                    if each_connection.status_colour == intermediate_colour:
                        next_shape_colour = intermediate_colour
                    if each_connection.status_colour == bad_colour:
                        next_shape_colour = bad_colour
        except:
            next_shape_colour = bad_colour
        next_shape_origin = get_shape_origins(shapes_to_draw_class[-1].origin)
        shapes_to_draw_class.append(ShapeAlerts(next_shape_origin, next_shape_colour, ''))
        shapes_to_draw_class = list_limit(shapes_to_draw_class, 9)
        return

    def write_system_health(self):
        # Text Writing and positioning code
        self.draw.text((self.cpu_start, 30), self.cpu.temp + ' | ', font=font, fill=self.cpu.device_status)
        self.draw.text((self.gpu_start, 30), self.gpu.temp + ' | ', font=font, fill=self.gpu.device_status)
        self.draw.text((self.ze_time_start, 30), self.ze_time + ' | ', font=font, fill=good_colour)
        self.draw.text((self.ip_address_start, 30), self.ip_address[0], font=font, fill=self.ip_address[1])
        self.draw.text((10, 30), 'hello Dwane', font=font, fill=good_colour)
        return

    def write_server_health(self):
        server_box_line_start = 60  # Where the output of users on first server starts (y-axis)
        for each_server_output in server_output:
            # Write server name
            self.draw.text((10, server_box_line_start), each_server_output.host, font=font_small, fill=good_colour)

            # Discover how long the longest user name line is
            x_max_user_text_size = self.draw.textsize(each_server_output.host, font=font_small)[0]

            # Discover where to start writing user names
            user_text_start = (server_box_line_start + (self.draw.textsize(each_server_output.host, font=font)[1])*2)

            # Spacing between users (y-axis)
            user_box_line_spacing = 2

            # Current position to write a user line (y-axis)
            user_text_cur = user_text_start + user_box_line_spacing

            # Write each user line then discover and set where next line should be written
            for each_user in each_server_output.users:
                self.draw.text((10, user_text_cur), str("[User] %s | [IP] %s" % (each_user.user_name, each_user.ip)), font=font_small, fill=good_colour)
                user_text_cur += (self.draw.textsize(str(each_user.user_name), font=font_small)[1]*2 + user_box_line_spacing)

                cur_user_text_size = self.draw.textsize(str("[User] %s | [IP] %s" % (each_user.user_name, each_user.ip)), font=font_small)[0]
                if cur_user_text_size > x_max_user_text_size:
                    x_max_user_text_size = cur_user_text_size

            # define where a box should be drawn around the users
            user_box_lines = [(10, user_text_start), (10+x_max_user_text_size, user_text_cur)]

            # Draw a box around the users
            self.draw.rectangle(user_box_lines, outline=good_colour)

            # Discover where to start the next servers user box
            server_box_line_start = user_text_cur + self.draw.textsize("derp", font=font_small)[1]*2
        return

    def write_endpoint_health(self):
        # Write the output for all cisco connections
        dsl_counter = 1
        for each_ssh_connection in cisco_connections:
            each_dsl_start = 1.8 - (dsl_counter * 0.2)
            self.draw.text((self.dsl_start[dsl_counter - 1], height/each_dsl_start), str(each_ssh_connection.ze_output),
                           font=font, fill=each_ssh_connection.status_colour)
            dsl_counter += 1
        return


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
        local_server_output.append(SystemLog(ze_args[0], ze_args[1], ze_args[2], ze_args[3]))
        q.task_done()


# Manages end point connection threads
def end_point_con(q, local_ssh_connections):
    while True:
        if q.empty() is True:
            break
        ze_args = (q.get())
        ze_args = ze_args.split("|")
        ssh = (SSH(ze_args[0], ze_args[1], ze_args[2]))
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
good_colour = '#00AA00'
intermediate_colour = '#FFA500'
bad_colour = '#FF0000'

shape_origin = (width * .8, height * .91)

# Send captured SIGINT's to signal handler function to allow for a graceful exit
signal.signal(signal.SIGINT, signal_handler)
shapes_to_draw_class = [ShapeAlerts(shape_origin, 0, ""), ]


def main():
    count = 0

    createImage = CreateImage(count)
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
