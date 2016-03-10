import signal
import curses
from  main import *
import inspect
import itertools

# Global variables
exit_flag = False
debug_flag = 0

# read_config()


# Set exit flag to exit checked when the time is right to exit gracefully
def signal_handler(signal, frame):
    global exit_flag
    print('[!!!] Exiting gracefully')
    exit_flag = True

# Send captured SIGINT to signal handler function to allow for a graceful exit
signal.signal(signal.SIGINT, signal_handler)


# Class to format data and print out the ui etc
class box_data:
    def __init__(self, data_set, title):
        global x_cur_pos, y_cur_pos

        self.title = title
        self.title_whitespace = ' '*(int((width/2)-int(len(self.title)/2))-2)

        # Set colours to use
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW)
        curses.use_default_colors()

        # Add title
        stdscr.addstr(x_cur_pos, y_cur_pos, self.title_whitespace + self.title + self.title_whitespace, curses.color_pair(1))
        x_cur_pos += 1

        # Check the data set for the data type and make a decision on how to format it with that data
        for each_string in data_set:
            if type(each_string) == str:
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
                        stdscr.addstr(x_cur_pos, y_cur_pos,  self.get_white_space(str(each_member[1])) + (str(each_member[1])) +
                                      self.get_white_space(str(each_member[1])), curses.color_pair(2))
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
                                        stdscr.addstr(x_cur_pos, y_cur_pos+len(each_member_t3.user_name)+3, (str(each_member_t3.pty)))
                                        stdscr.addstr(x_cur_pos, y_cur_pos+len(each_member_t3.user_name)+len(each_member_t3.pty) + 6, (str(each_member_t3.ip)))
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
        return

    # Find the amount of white space on either end of a string for highlighting the entire line
    def get_white_space(self, string):
        white_space_string = ' '*(int((width/2)-int(len(string)/2))-2)
        return white_space_string


def local_main():
    global height, width, stdscr, y_cur_pos, x_cur_pos
    count = 0
    server_q = Queue(maxsize=2)
    end_point_q = Queue(maxsize=2)

    stdscr = curses.initscr()

    curses.noecho()
    stdscr.keypad(True)

    while True:
        height, width = stdscr.getmaxyx()

        # Set where the cursor should start
        y_cur_pos = 2
        x_cur_pos = 2

        # Create external connections and retrieve data
        server_output, cisco_connections = runserver_threaded_connections(server_q, end_point_q)

        # Get local data
        createImage = CreateImage(count)
        ze_time = createImage.get_time()
        ip_address = createImage.get_ip_address()
        createImage.reset_system_health()

        cpu = '[%s] %s c' % (createImage.cpu.device_name, createImage.cpu.temp)
        gpu = '[%s] %s c' % (createImage.gpu.device_name, createImage.gpu.temp)
        system_strings_to_write = [ze_time, ip_address,cpu, gpu]

        stdscr.erase()
        stdscr.border(0)
        try:
            box_data(system_strings_to_write, 'System Health')
            box_data(server_output, 'Servers')
            box_data(cisco_connections, 'Endpoints')

            stdscr.refresh()
            count += 1

        # If we have an error assume the window is too small, don't think this is te right idea but working?!!?
        except:
            stdscr.addstr(x_cur_pos, y_cur_pos, 'Window is too small')

        # Check if we want to exit, if so run commands to exit gracefully
        if exit_flag is True:
                curses.nocbreak()
                stdscr.keypad(False)
                curses.echo()
                curses.endwin()
                exit(0)

if __name__ == '__main__':
    local_main()
