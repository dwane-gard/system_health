from PIL import Image, ImageFont, ImageDraw
from queue import Queue
from urllib.request import urlopen
import time
import socket
import math
from SystemInformation import DeviceData
from ExternalConnection import CiscoConnections, LinuxConnection


good_colour = '#00AA00'
intermediate_colour = '#FFA500'
bad_colour = '#FF0000'
width = 1920
height = 1080
font = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 26)
font_small = ImageFont.truetype('fonts/UbuntuMono-R.ttf', 20)
shape_origin = (width * .8, height * .91)

class DrawImage:
    def __init__(self, count, cisco_connections, server_output):

        self.cisco_connections = cisco_connections
        self.server_output = server_output
        self.deviceData = DeviceData()

        self.image = Image.new('RGB', (width, height))
        self.draw = ImageDraw.Draw(self.image)
        # self.count = 0

        self.ze_time = None
        self.ip_address = None
        self.pub_ip_address = None
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
        self.get_public_ip_address()
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

    def get_public_ip_address(self):
        try:
            pub_ip_address = (urlopen('http://ip.42.pl/short').read()).decode('utf-8')
            pub_ip_address = '[Public IP] %s' % pub_ip_address
            self.pub_ip_address = pub_ip_address, good_colour
        except:
            pub_ip_address = "[Public IP] No Connection"
            self.pub_ip_address = pub_ip_address, intermediate_colour
        return pub_ip_address

    def get_font_size(self):
        self.cpu_size = self.draw.textsize(self.cpu.temp, font)[0]
        self.gpu_size = self.draw.textsize(self.gpu.temp, font)[0]

        self.ip_address_size = self.draw.textsize(self.ip_address[0], font)[0]
        self.ze_time_size = self.draw.textsize(self.ze_time, font)[0]

        self.first_line_tot_pos = self.cpu_size + self.int_pos + self.gpu_size\
                                  + self.int_pos + self.ze_time_size + self.int_pos\
                                  + self.ip_address_size + self.int_pos

        for each_connection in self.cisco_connections:
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
            for each_connection in self.cisco_connections:
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
        for each_server_output in self.server_output:
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
        for each_ssh_connection in self.cisco_connections:
            each_dsl_start = 1.8 - (dsl_counter * 0.2)
            self.draw.text((self.dsl_start[dsl_counter - 1], height/each_dsl_start), str(each_ssh_connection.ze_output),
                           font=font, fill=each_ssh_connection.status_colour)
            dsl_counter += 1
        return


# holds information to draw hexagon pattern that indicates recent error history
class ShapeAlerts:
    def __init__(self, origin, error_case, error_message):
        self.origin = origin
        self.error_case = error_case
        self.error_message = error_message


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
