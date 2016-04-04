import subprocess
import time
import socket
from urllib.request import urlopen
from queue import Queue

good_colour = '#00AA00'
intermediate_colour = '#FFA500'
bad_colour = '#FF0000'


class LocalData:
    def __init__(self, count, cisco_connections, server_output):

        self.cisco_connections = cisco_connections
        self.server_output = server_output
        self.deviceData = DeviceData()

        self.ze_time = None
        self.ip_address = None
        self.pub_ip_address = None
        self.gpu = None
        self.cpu = None

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
        # Get system health from local system
        for each_device in self.deviceData.devices:
            each_device.cat_temp()
            each_device.get_device_status()
            if each_device.device_type == 'CPU':
                self.cpu = each_device
            if each_device.device_type == 'GPU':
                self.gpu = each_device


        self.get_public_ip_address()
        self.get_ip_address()
        self.get_time()

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

    def get_public_ip_address(self):
        try:
            pub_ip_address = (urlopen('http://ip.42.pl/short').read()).decode('utf-8')
            pub_ip_address = '[Public IP] %s' % pub_ip_address
            self.pub_ip_address = pub_ip_address, good_colour
        except:
            pub_ip_address = "[Public IP] No Connection"
            self.pub_ip_address = pub_ip_address, intermediate_colour
        return pub_ip_address

class DeviceData:
    def __init__(self, debug_flag=0):
        self.dirs = self.get_dir_ls()
        self.debug_flag = debug_flag
        # If a hwmon device is a gpu or a cpu add it to the list
        self.devices = [self.EachDevice(each_dir) for each_dir in self.dirs
                        if self.EachDevice(each_dir).device_type == 'GPU' or 'CPU']

    def get_dir_ls(self):
        # Get a list of all the dirs in hwmon
        proc = subprocess.check_output(['ls', '/sys/class/hwmon']).rstrip()
        output = proc.split(b'\n')
        return output

    class EachDevice:
        def __init__(self, ze_dir, debug_flag=0):

            self.debug_flag = debug_flag

            if self.debug_flag == 1:
                print('[+] Intilizing device')
            self.ze_dir = ze_dir
            try:
                self.vendor_id, self.device_id = self.identify_dir(ze_dir)
            except:
                self.device_type = b'Unknown'
                if self.debug_flag == 1:
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
                if self.debug_flag == 1:
                    print(e)
                pass
            except IndexError as e:
                if self.debug_flag == 1:
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
                if self.debug_flag == 1:
                    print('[!] Cannot Read Temp of device %s' % ze_dir)
                self.temp_input = 0
                self.temp = '0'

