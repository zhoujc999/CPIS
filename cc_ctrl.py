import socket
import sys
import select
import platform
import time
from math import pi
from time import sleep
import pidcontroller
from os import path
import fcntl
from common import *

ENG_CTL_HOST = "10.0.0.2"
ENG_CTL_PORT = 53599
pid = pidcontroller.PID(1, 0.1, 1)

connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
eprint("\n Connecting to engine controller on %s:%s" %
      (ENG_CTL_HOST, str(ENG_CTL_PORT)))

# Init file
if not path.exists("set_speed.txt"):
    with open('set_speed.txt', 'w') as f:
        f.write("50")

while(1):
    try:
        connection_socket.connect((ENG_CTL_HOST, ENG_CTL_PORT))
    except ConnectionRefusedError:
        sleep(0.5)
        continue
    else:
        break
    
eprint("Connected.")



cur_speed = 0.0
set_speed = 0
cur_pref_accel = 0.1
cur_pref_accel_diff = 0.1
while True:
    # Get cur_speed from vehicle simulator (in kmh)
    cur_speed = read_file('cur_speed.txt', float)
    tprint("Cur_Spd %.2f" % (cur_speed))
    set_speed = read_file('set_speed.txt', int)
    tprint("Set_Spd %d" % (set_speed))

    # Calculate prefered acceleration & deacceleration
    diff = set_speed - cur_speed
    prefered_accel = pid.Update(diff, dt=UPDATE_FREQ, ci_limit_L=-10, ci_limit_H=200) / 20
    
    # Training Mode
    if (FORCE_TRAINING):
        cur_pref_accel += cur_pref_accel_diff
        if cur_pref_accel > 2.1:
            cur_pref_accel_diff = -cur_pref_accel_diff
        elif cur_pref_accel < -0.1:
            cur_pref_accel_diff = -cur_pref_accel_diff
        prefered_accel = cur_pref_accel
        eprint("(Force Training Mode)")

    tprint("Pref_Accel %.2f" % (prefered_accel))
    eprint("Prefered Acceleration %.2f" % (prefered_accel))
    payload_serialize = str.encode("%+.2f" % (prefered_accel))
    connection_socket.send(payload_serialize)
    # eprint("Payload delivered\n")
    time.sleep(1.0 / UPDATE_FREQ)

connection_socket.close()
