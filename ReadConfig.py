#!/usr/bin/python3

import sys, os

class ReadConfig:
    def __init__(self, rules, debug_flag=0, conf_string=None, conf_file_name=None):
        self.debug_flag = debug_flag
        self.conf_file_name = conf_file_name
        self.conf_string = conf_string
        self.rules = rules
        self.multi_line_rules = [x for x in self.rules if '{' in x]

        # self.multiLineRules = [self.MultiLineRule(x) for x in self.multi_line_rules]
        self.singe_line_rules = [x for x in self.rules if '{' not in x]
        self.store = []

        if not conf_string:
            if conf_file_name:
                self.retrieve_file(self.conf_file_name)
            elif __name__ == '__main__':
                print('[!] No configuration found!')
                exit(0)
            else:
                if debug_flag == 1:
                    print('[!] No configuration found!')
        self.parse(self.conf_string)

    def print_rules(self):
        print('[+] Output:')
        for each in self.store:
            if each.__class__.__name__ == 'Rule':
                print('Single Line rule:')
                print(each.rule, each.conf)
                print('_'*5)
            elif each.__class__.__name__ == 'MultiLineRule':
                print('Multi line rule')
                print(each.rule)
                print(each.rule_label)
                for each_rule in each.subRules:
                    print('[%s]%s' % (each_rule.rule, each_rule.conf))
                print('_'*5)
            else:
                print('[Fail]')

    def retrieve_file(self, conf_file_name):
        with open(conf_file_name, 'r') as conf:
            conf = conf.read()
            self.conf_string = conf
            return conf

    def parse(self, conf_string):

        conf = conf_string.split('\n')
        conf = [x.strip() for x in conf]
        conf = [x for x in conf if x is not '']

        open_rule = False
        for line in conf:

            # If comment line go on to next line
            if line.startswith('#'):
                continue

            if open_rule is True:
                if '}' in line:
                    open_rule = False
                    self.store.append(working_multi_line_rule)
                    pass
                else:
                    working_multi_line_rule.subRules.append(working_multi_line_rule.SubRule(line))

            elif '{' in line:
                open_rule = True
                working_multi_line_rule = self.MultiLineRule(line)

            else:
                working_rule, working_conf = line.split('=')
                for each_rule in self.singe_line_rules:

                    if working_rule == each_rule:
                        self.store.append(self.Rule(working_rule, working_conf))




    class Rule:
        def __init__(self, rule, conf):
            self.rule = rule
            self.conf = conf
            return



    class MultiLineRule:
        def __init__(self, raw_rule):
            self.rule, self.sub_rule = raw_rule.split('{')

            self.rule, self.rule_label = self.rule.split('=')
            self.sub_rule = self.sub_rule.rstrip('}')
            self.sub_rule = self.sub_rule.split(',')
            # subRules = [self.SubRule(x) for x in self.sub_rule]
            self.subRules = []

        class SubRule:
            def __init__(self, raw_rule):
                self.rule, self.conf = raw_rule.split('=')








if __name__ == '__main__':
    rules = ['height', 'width', 'good_colour', 'bad_colour', 'intermediate_colour',
             'cisco_device{password,user,host}', 'server_device{password,user,host,port}']

    conf = \
        '''
        # this is a comment
        height=1080
        width=1920


        '''
    readConfig = ReadConfig(rules=rules, debug_flag=0, conf_file_name='conf')
    readConfig.print_rules()


# # Read the config file or create one if it does not exist
# def read_config():
#     global cisco_devices, server_devices
#     global width
#     global height
#     global good_colour
#     global intermediate_colour
#     global bad_colour
#
#     device = ''
#     device_settings = []
#     cisco_devices = []
#     server_devices = []
#
#     # Check if conf file exist, if not create it
#     if not os.path.exists('conf'):
#         open('conf', 'w').write('# Configuration file for dynamic_background_generator\n'
#                                 '# Written by Dwane Gard\n\n'
#                                 'cisco_device=\t{\n'
#                                 '\tpassword=\n'
#                                 '\tuser=\n'
#                                 '\thost=\n'
#                                 '\tport=\n'
#                                 '}\n'
#                                 'server-device=\t{\n'
#                                 '\tpassword=\n'
#                                 '\tuser=\n'
#                                 '\thost=\n'
#                                 '\tport=\n'
#                                 '}\n'
#                                 'height=\n'
#                                 'width=\n'
#                                 'good_colour=#00AA00\n'
#                                 'intermediate_colour=#FFA500\n'
#                                 'bad_colour=#FF0000\n')
#
#     # Open and read the conf file
#     with open('conf', 'r') as configuration:
#         configuration = configuration.read()
#         configuration_as_list = configuration.split("\n")
#
#         cisco_config_open = False
#         server_config_open = False
#         for each_line in configuration_as_list:
#             if each_line.startswith('#'):
#                 continue
#             # Find each cisco or server device and record each line as a setting
#             if each_line.startswith('cisco_device='):
#                 cisco_config_open = True
#                 device = (each_line.split('=')[1])
#                 try:
#                     device = device.split('}')[0]
#                 except:
#                     pass
#
#             if each_line.startswith('server_device='):
#                 server_config_open = True
#                 device = (each_line.split('=')[1])
#                 try:
#                     device = device.split('}')[0]
#                 except:
#                     pass
#
#             device_settings.append(each_line)
#
#             if debug_flag == 1:
#                 print('[device] %s' % device)
#                 print('[device_settings] %s' % device_settings)
#
#             # When the '}' is found package the settings and add them to the list of devices
#             if '}' in each_line:
#                 if debug_flag == 1:
#                     if server_config_open:
#                         print('Ending Server %s' % device)
#                     if cisco_config_open:
#                         print('[+] Finalizing cisco device %s' % device)
#                 if cisco_config_open is True:
#                     cisco_devices.append(CiscoDevices(device, device_settings))
#                     cisco_config_open = False
#                     del device_settings[:]
#                     # device_settings.clear()
#
#                 elif server_config_open is True:
#                     server_devices.append(ServerDevices(device, device_settings))
#                     server_config_open = False
#                     del device_settings[:]
#                     # device_settings.clear()
#
#             # Find the other settings and apply them where necessary
#             elif each_line.startswith('height='):
#                 height = each_line.split('=')[1]
#                 height = int(height)
#             elif each_line.startswith('width='):
#                 width = each_line.split('=')[1]
#                 width = int(width)
#             elif each_line.startswith('good_colour='):
#                 good_colour = each_line.split('=')[1]
#             elif each_line.startswith('intermediate_colour='):
#                 intermediate_colour = each_line.split('=')[1]
#             elif each_line.startswith('bad_colour='):
#                 bad_colour = each_line.split('=')[1]
#
#         if device == '':
#             print('[!] Configuration File not configured!\n'
#                   'Creating File "conf" in script directory.\n'
#                   'Populate with:\n'
#                   'cisco_device=\t{\n'
#                   '\tpassword=\n'
#                   '\tuser=\n'
#                   '\thost=\n'
#                   '}\n'
#                   'server-device=\t{\n'
#                   '\tpassword=\n'
#                   '\tuser=\n'
#                   '\thost=\n'
#                   '\tport=\n'
#                   '}\n'
#                   'height=\n'
#                   'width=\n'
#                   'good_colour=#00AA00\n'
#                   'intermediate_colour=#FFA500\n'
#                   'bad_colour=#FF0000\n')
#             sys.exit()
#     if debug_flag == 1:
#         print('[cisco_settings] %s' % cisco_devices)
#         print('[server_devices] %s' % server_devices)

