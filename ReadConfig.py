#!/usr/bin/python3

import sys, os

class ReadConfig:
    def __init__(self, rules, debug_flag=0, conf_string=None, conf_file_name=None):
        self.debug_flag = debug_flag
        self.conf_file_name = conf_file_name
        self.conf_string = conf_string
        self.rules = rules
        self.store = []


    def print_rules(self):
        for each in self.store:
            print(each.rule, each.conf)

    def retrieve_file(self, conf_file_name):
        with open(conf_file_name, 'r').read() as conf:
            self.conf_string = conf

    def parse(self, conf_string):
        conf = conf_string.split('\n')
        open_rule = False
        for line in conf:
            if line.startswith('#'):
                continue
            elif open_rule is True:

            elif '}' in line:
                open_rule = False
                # finish the working line and add vars to class
                pass
            else:
                working_line = line
                working_rule, working_conf = working_line.split('=')
                for each_rule in self.rules:
                    if working_rule == each_rule:
                        if '{' in each_rule:
                            open_rule = True
                            continue
                        else:
                            self.Store(working_rule, working_conf)
                            continue

    class Store:
        def __init__(self, rule, conf):
            self.rule = rule
            self.conf = conf
            return

    class StoreWithCat:
        def __init__(self, rule_cat, rule, conf):
            self.rule_cat = rule_cat
            self.store = []

            return

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


if __name__ == '__main__':
    readConfig = ReadConfig
    readConfig.print_rules()
