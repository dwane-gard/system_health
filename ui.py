#!/usr/bin/python3
from threading import Thread, Lock
import signal
from queue import Queue
"""
Simple script that displays system, server and endpoint data.
Requires:
    Python3.4 or Python2.7(some issues)
    PIL - Python Imaging Library
    feh
    pexpect
Written by Dwane Gard
"""

import curses
from start import runserver_threaded_connections, read_config
from DrawImage import DrawImage

import inspect
import subprocess

# Global variables
exit_flag = False
resize_flag = False
config_change_flag = False
debug_flag = 0
x_cur_pos, y_cur_pos = 0, 0
ze_lock = Lock()


# Set exit flag to exit checked when the time is right to exit gracefully
def signal_handler(signal, frame):
    global exit_flag
    if ze_lock is True:
        ze_lock.release()
    stdscr.clear()
    stdscr.refresh()
    print('[!!!] Exiting gracefully')
    exit_flag = True

# Send captured SIGINT to signal handler function to allow for a graceful exit
signal.signal(signal.SIGINT, signal_handler)


# Class to format data and print out the ui etc
class BoxData:
    def __init__(self, data_set, title, alignment=1):
        global x_cur_pos, y_cur_pos

        self.title = title
        self.title_whitespace = ' '*(int((width/2)-int(len(self.title)/2))-2)

        # Set colours to use
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.use_default_colors()

        # Add title
        stdscr.addstr(x_cur_pos, y_cur_pos, self.title_whitespace + self.title + self.title_whitespace,
                      curses.color_pair(1))
        x_cur_pos += 1

        # if alignment == right
        if alignment == 2:
            for each_string in data_set:
                if type(each_string) == str:
                    left_string, right_string = each_string.rsplit(']', 1)
                    right_y_cur_pos = width - len(right_string) - 4
                    stdscr.addstr(x_cur_pos, y_cur_pos, left_string + ']')
                    stdscr.addstr(x_cur_pos, right_y_cur_pos, right_string)
                    x_cur_pos += 1

                elif type(each_string) == bytes:
                    right_y_cur_pos = width - len(each_string)
                    stdscr.addstr(x_cur_pos, right_y_cur_pos, each_string)
                    x_cur_pos += 1
                else:
                    # Data set is incompatible with right alignment
                    alignment = 1

        # If alignment == left
        if alignment == 1:
            # Check the data set for the data type and make a decision on how to format it with that data
            for each_string in data_set:
                if type(each_string) == str:
                    stdscr.addstr(x_cur_pos, y_cur_pos, each_string)
                    x_cur_pos += 1

                elif type(each_string) == bytes:
                    stdscr.addstr(x_cur_pos, y_cur_pos, each_string)
                    x_cur_pos += 1

                # Don't think this choice is ever made?
                elif type(each_string) == list:
                    for each_string_t2 in each_string:
                        if type(each_string_t2) == str:
                            stdscr.addstr(x_cur_pos, y_cur_pos, each_string_t2)
                            x_cur_pos += 1
                        if type(each_string_t2) == list:
                            for each_string_t3 in each_string_t2:
                                if type(each_string_t3) == str:
                                    stdscr.addstr(x_cur_pos, y_cur_pos, each_string_t3)
                                    x_cur_pos += 1

                else:
                    for each_member in inspect.getmembers(each_string):

                        # Check if the data set is consistent with hosts and if so print them
                        if each_member[0] == 'host':
                            # Print data with a highlighted line
                            stdscr.addstr(x_cur_pos, y_cur_pos,  self.get_white_space(str(each_member[1])) +
                                          (str(each_member[1])) + self.get_white_space(str(each_member[1])),
                                          curses.color_pair(2))
                            x_cur_pos += 1

                        # Check if the data set is consistent with users and if so print them
                        elif each_member[0] == 'users':
                            for each_member_t2 in each_member:

                                # If there is data in the entry use it
                                if len(each_member_t2) > 0:

                                    # Break out the user data from the users list
                                    for each_member_t3 in each_member_t2:
                                        try:
                                            # Put each user inline with it's data
                                            stdscr.addstr(x_cur_pos, y_cur_pos, (str(each_member_t3.user_name)))
                                            stdscr.addstr(x_cur_pos, y_cur_pos+len(each_member_t3.user_name) +
                                                          3, (str(each_member_t3.pty)))
                                            stdscr.addstr(x_cur_pos, y_cur_pos+len(each_member_t3.user_name) +
                                                          len(each_member_t3.pty) + 6, (str(each_member_t3.ip)))
                                            x_cur_pos += 1
                                        except:
                                            pass
                                else:
                                    # If data doesn't exist assume there is no connection
                                    stdscr.addstr(x_cur_pos, y_cur_pos, "Can't connect to server", curses.color_pair(3))
                                    x_cur_pos += 1

                        # Check if the data set is consistent with endpoint connection and if so print them
                        elif each_member[0] == 'ze_output':

                            # If there is 'Dead' in the string assume it is a dead connection and highlight it as so
                            if 'Dead' in each_member[1]:
                                stdscr.addstr(x_cur_pos, y_cur_pos, (str(each_member[1])), curses.color_pair(3))
                                x_cur_pos += 1
                            else:
                                stdscr.addstr(x_cur_pos, y_cur_pos, (str(each_member[1])))
                                x_cur_pos += 1
            else:
                pass

    # Find the amount of white space on either end of a string for highlighting the entire line
    @staticmethod
    def get_white_space(string):
        white_space_string = ' '*(int((width/2)-int(len(string)/2))-2)
        return white_space_string


class Menu:
    def __init__(self):
        global resize_flag, config_change_flag

        # Set colours to use
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.use_default_colors()

        while True:
            c = stdscr.getch()
            if c == curses.KEY_RESIZE:
                resize_flag = True

            if c == ord('z'):
                ze_lock.acquire()

                # Call vim to edit the local configuration file
                subprocess.call(['vim', 'conf'])

                config_change_flag = True
                stdscr.erase()
                curse_print('[+] Reloading Interface', curses.color_pair(1), 2, 2, stdscr)
                stdscr.refresh()

                # Reread the configuration file
                read_config()
                ze_lock.release()
            if c == ord('x'):
                # ze_lock.acquire()
                # open_dialog_box = (DialogBox(['derp', 'derp', 'derp']))
                # open_dialog_box.build()
                # open_dialog_box.use()
                stdscr.addstr(x_cur_pos, y_cur_pos, "Going on with my life", curses.color_pair(3))
            if c == ord('c'):
                stdscr.addstr(x_cur_pos, y_cur_pos, "Going on with my life", curses.color_pair(3))

    @staticmethod
    def print_menu():
        menu_cur = 2
        menu_cur = curse_print('z ', curses.color_pair(1), menu_cur, height-4, stdscr)
        menu_cur = curse_print("Edit Configuration", curses.color_pair(2), menu_cur, height-4, stdscr)
        menu_cur = curse_print(' | ', curses.color_pair(2), menu_cur, height-4, stdscr)
        menu_cur = curse_print('x ', curses.color_pair(1), menu_cur, height-4, stdscr)
        menu_cur = curse_print("Go on with your life", curses.color_pair(2), menu_cur, height-4, stdscr)
        menu_cur = curse_print(' | ', curses.color_pair(2), menu_cur, height-4, stdscr)
        menu_cur = curse_print('c ', curses.color_pair(1), menu_cur, height-4, stdscr)
        menu_cur = curse_print("Go on with your life", curses.color_pair(2), menu_cur, height-4, stdscr)
        return menu_cur


class DialogBox:
    def __init__(self, options):
        self.options = options
        self.dialog_origin = height/2, width/2
        self.req_lines = int(len(options) + 10)
        self.req_collums = int(len(max(options)) + 10)

        self.dialog_height_start = int(self.dialog_origin[0] - self.req_collums/2)
        self.dialog_height_end = int(self.dialog_origin[0] + self.req_collums/2)
        self.dialog_width_start = int(self.dialog_origin[1] - self.req_lines/2)
        self.dialog_width_end = int(self.dialog_origin[1] + self.req_lines/2)
        self.text_start = self.dialog_height_start-2, self.dialog_width_start - 2
        self.window = curses.newwin(self.req_lines, self.req_collums, self.dialog_height_start, self.dialog_width_start)
        self.window.border()
        self.y_cur = 2
        self.x_cur = 2

    def build(self):
        self.window = curses.newwin(self.req_lines, self.req_collums, self.dialog_height_start, self.dialog_width_start)
        self.window.border()
        self.y_cur = 2
        self.x_cur = 2

        for each_option in self.options:
            x_cur = curse_print(each_option, curses.color_pair(3), self.x_cur, self.y_cur, self.window)
            self.y_cur += 1
        self.window.refresh()
        return

    def use(self):
        # curses.echo()
        c2 = stdscr.getch()
        if c2 == 27:
            self.close()
            stdscr.refresh()
            ze_lock.release()

    def close(self):
        self.window.erase()


def curse_print(ze_string, colour_pair, x_cur, y_cur, window):
    window.addstr(int(y_cur), int(x_cur), ze_string, colour_pair)
    x_cur += len(ze_string)
    return x_cur


def local_main():
    global height, width, stdscr, y_cur_pos, x_cur_pos, resize_flag, config_change_flag
    count = 0
    server_q = Queue(maxsize=2)
    end_point_q = Queue(maxsize=2)

    stdscr = curses.initscr()
    height, width = stdscr.getmaxyx()
    curses.noecho()
    stdscr.keypad(True)

    menu = Thread(target=Menu)
    menu.setDaemon(True)
    menu.start()

    while True:
        ze_breakable_loop = True
        while ze_breakable_loop is True:
            height, width = stdscr.getmaxyx()

            # Set where the cursor should start
            y_cur_pos = 2
            x_cur_pos = 2

            # Create external connections and retrieve data
            config_change_flag = False
            server_output, cisco_connections = runserver_threaded_connections(server_q, end_point_q)

            # Get local data
            createImage = DrawImage(count, cisco_connections, server_output)
            ze_time = createImage.get_time()
            ip_address = createImage.get_ip_address()
            public_ip_address = createImage.get_public_ip_address()

            createImage.reset_system_health()

            cpu = '[%s] %s c' % (createImage.cpu.device_name, createImage.cpu.temp)
            gpu = '[%s] %s c' % (createImage.gpu.device_name, createImage.gpu.temp)
            system_strings_to_write = [ze_time, ip_address, public_ip_address, cpu, gpu]

            ze_lock.acquire()

            # If config has changed while loading restart loop
            if config_change_flag is True:
                if ze_lock:
                    ze_lock.release()
                config_change_flag = False
                break

            if resize_flag is True:
                if ze_lock:
                    ze_lock.release()
                curses.resizeterm(height, width)
                resize_flag = False
                break

            stdscr.erase()
            stdscr.border(0)
            # try:
            BoxData(system_strings_to_write, 'System Health', 2)
            BoxData(server_output, 'Servers')
            BoxData(cisco_connections, 'Endpoints')
            Menu.print_menu()

            stdscr.refresh()
            count += 1

            # If we have an error assume the window is too small, don't think this is te right idea but working?!!?
            # except:
            #     stdscr.addstr(x_cur_pos, y_cur_pos, 'Window is too small')
            # finally:
            ze_lock.release()

            # Check if we want to exit, if so run commands to exit gracefully
            if exit_flag is True:
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
                curses.endwin()
                exit(0)

if __name__ == '__main__':
    local_main()
