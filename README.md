# system_health

Python script to display system, server and endpoint health either as wallpaper or an curses ui.

## Requirements:
- Linux Operationg system
- Python 3.4+
- Pexpect
- feh

## Configuration
- After the first unscucessful run the script will create a file in the scripts directory called 'conf'. Edit this file with the desired parramaters for example:

~~~text
# Configuration file for dynamic_background_generator
# Written by Dwane Gard
cisco_device='name of cisco device'{
  password='password'
  user='user name'
  host='host name or ip'
}
server-device='name of server'{
  password='password'
  user='user name'
  host='host name or ip'
  port='port number'
}

height=1080
width=1920
good_colour=#00AA00
intermediate_colour=#FFA500
bad_colour=#FF0000
~~~


## How to run
~~~bash

  
  # To generate and display wallpapers with system data
  python3 main.py
  
  # To generate an curses interface with system data
  python3 ui.py
~~~
