#!/usr/bin/python3

'''
A simple configuration parser.
See last function for how to use.
Written by Dwane Gard
'''

class ReadConfig:
    def __init__(self, rules, debug_flag=0, conf_string=None, conf_file_name=None):
        self.debug_flag = debug_flag
        self.conf_file_name = conf_file_name
        self.conf_string = conf_string
        self.rules = rules
        self.multi_line_rules = [x for x in self.rules if '{' in x]
        self.singe_line_rules = [x for x in self.rules if '{' not in x]
        self.store = []

        if not conf_string:
            if conf_file_name:
                self.retrieve_file(self.conf_file_name)
            elif __name__ == '__main__':
                print('[!] No configuration found!')
                exit(0)
            else:
                # if debug_flag == 1:
                print('[!] No configuration found!')
                exit(1)
        self.parse(self.conf_string)

    # Output the rules as classes
    def output(self):
        single_line_rules = [x for x in self.store if 'Rule' == x.__class__.__name__]
        multi_line_rules = [x for x in self.store if 'MultiLineRule' == x.__class__.__name__]

        return single_line_rules, multi_line_rules

    # Output the rules using print
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

    # Retrieve the configuration file and return the string of it
    def retrieve_file(self, conf_file_name):
        with open(conf_file_name, 'r') as conf:
            conf = conf.read()
            self.conf_string = conf
            return conf

    # Parse over the configuration string separating and storing  into relevant classes
    def parse(self, conf_string):
        conf = conf_string.split('\n')
        conf = [x.strip() for x in conf]
        conf = [x for x in conf if x is not '']

        open_rule = False
        for line in conf:

            # If comment line go on to next line
            if line.startswith('#'):
                continue

            # If we are currently looking at a multi line rule
            if open_rule is True:

                # If the multi-line rule is closing
                if '}' in line:
                    open_rule = False
                    self.store.append(working_multi_line_rule)
                    pass

                # If it is a line of a multi-line rule add it as a sub rule
                else:
                    working_multi_line_rule.subRules.append(working_multi_line_rule.SubRule(line))

            # If we see the beginning of a multi-line rule
            elif '{' in line:
                open_rule = True
                working_multi_line_rule = self.MultiLineRule(line)

            # If  it is a single line rule
            elif '=' in line:
                working_rule, working_conf = line.split('=')
                for each_rule in self.singe_line_rules:

                    if working_rule == each_rule:
                        self.store.append(self.Rule(working_rule, working_conf))

            # If the line doesn't fit any known type
            else:
                continue

    # for storing single rules
    class Rule:
        def __init__(self, rule, conf):
            self.rule = rule
            self.conf = conf
            return

    # for storing multi-rules
    class MultiLineRule:
        def __init__(self, raw_rule):
            self.rule, self.sub_rule = raw_rule.split('{')
            self.rule, self.rule_label = self.rule.split('=')
            self.sub_rule = self.sub_rule.rstrip('}')
            self.sub_rule = self.sub_rule.split(',')
            self.subRules = []

        class SubRule:
            def __init__(self, raw_rule):
                self.rule, self.conf = raw_rule.split('=')


if __name__ == '__main__':
    # a List of rules for example:
    # rules = ['good_colour', 'intermediate_colour', 'bad_colour', 'width', 'height',
    #        'cisco_device{password,user,host}', 'server_device{password,user,host,port}']
    rules = []

    # A configuration file
    conf = ''
    readConfig = ReadConfig(rules=rules, debug_flag=0, conf_file_name='conf')

    # Will provide a printed output for troubleshooting
    readConfig.print_rules()

    # Will output the rules in 2 lists of classes separated as multi line and single line
    # See class MultiLineRule and class SingleLineRule for structure
    readConfig.output()

