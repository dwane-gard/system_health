import pexpect
from pexpect import pxssh


# Gets DSL info from cisco 877 or 887
class CiscoConnections:
    def __init__(self, host, user, passwd, debug_flag=0, good_colour='#00AA00', bad_colour='#FF0000'):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.ze_output = ""
        self.debug_flag = debug_flag
        self.status_colour = good_colour
        self.bad_colour = bad_colour
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


    def output(self):
        self.status = ('[%s] ' % self.host) + self.status

        self.download = self.download.strip()
        self.download = '[DL] ' + self.download

        self.upload = self.upload.strip()
        self.upload = '[UL] ' + self.upload

        self.crc = self.crc.strip()
        self.crc = '[Errors] ' + self.crc

        self.ze_output = " | ".join([self.status, self.download, self.upload, self.crc])
        if self.debug_flag == 1:
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
            self.status_colour = self.bad_colour
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
class LinuxConnection:
    def __init__(self, host, user, passwd, port, debug_flag=0):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        self.users = []
        self.debug_flag = debug_flag
        try:
            self.ssh = self.connection()

        except Exception:
            if self.debug_flag == 1:
                print('[!] Error connectiong to server: %s' % self.host)

            return

        # self.get_auth(self.ssh)
        if self.ssh:
            self.get_current_users(self.ssh)

            self.close_connection(self.ssh)

        if debug_flag == 1:
            print('[+] Connections to servers')
            print('[User@Host] %s@%s' % (self.user, self.host))

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
        # s.prompt()
        return s

    # check who last accesed server (prety useless think it will always be this script as it reconnects constantly)
    def get_auth(self, connection):
        connection.sendline('cat /var/log/lastlog')
        connection.prompt()
        last_connection_ip = connection.before
        ze_derp = last_connection_ip.strip()
        if self.debug_flag == 1:
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
