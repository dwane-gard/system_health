# system_health

Python script to display system, server and endpoint health either as an curses ui.

## Requirements:
- Linux Operationg System
- Python 3.4+
- Pexpect
- Vim

## Configuration
- Create a file named conf in the programs directory with the bellow structure

~~~text
  # Configuration file for dynamic_background_generator
  cisco_device=<name of cisco device>{
    password=<password>
    user=<user name>
    host=<host name or ip>
  }
  server-device=<name of server>{
    password=<password>
    user=<user name>
    host=<host name or ip>
    port=<port number>
  }

  good_colour=#00AA00
  intermediate_colour=#FFA500
  bad_colour=#FF0000
~~~


## How to run
~~~bash

  # To generate an curses interface with system data
  python3 system_health.py
~~~
