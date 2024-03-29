import socket
import sys
import select
import time
from math import pi
from time import sleep
import pidcontroller
from os import path
import fcntl
from common import *


HOST = '0.0.0.0'
PORT = 53599

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', PORT))

server_socket.listen(5)
eprint("\n Listning on port: " + str(PORT))

client_socket, (client_ip, client_port) = server_socket.accept()
eprint("\n Client" + client_ip + "connected successfully\n")

throttle = 0.0
new_gear = gear = 1
rpm = 0
brake = False
delay_count = 10
while True:
    in_payload = client_socket.recv(104) # revist
    if not in_payload:
        break
    prefered_accel = in_payload.decode()
    prefered_accel = float(prefered_accel)
    # deserialize
    # payload = in_payload.split()
    # print(prefered_accel)
    
    # Read rpm from simulation
    rpm = read_file('rpm.txt', int)
    tprint("RPM %d" % (rpm))

    # Engine control
    if prefered_accel > THROTTLE_SCALE:
        throttle = 1.0
    elif prefered_accel < 0.0:
        throttle = 0.0
    else:
        throttle = preferred_accel_to_accel(prefered_accel) # prefered_accel
    tprint("Throttle %.2f" % (throttle))

    # Brake control
    if preferred_accel_to_brake(prefered_accel):
        brake = True
    else:
        brake = False

    # Shift down & shift up RPM
    if FORCE_DATA_MODEL_TRAINING:
        mapping = [1000, 3500]
    elif (throttle > 0.9):
        mapping = [4500, 7000]
    else:
        mapping = [1100, 3000]
    if rpm > mapping[1]:
        new_gear = min(5, gear+1)
    elif rpm < mapping[0]:
        new_gear = max(1, gear-1)
    
    # Gear change delay
    if (new_gear != gear):
        if (delay_count <= 0):
            gear = new_gear
            delay_count = 10
        else:
            delay_count -= 1

    # Overriding
    ovwr_gear = read_file('override_gear.txt', int)
    if (5 >= ovwr_gear > 0):
        gear = ovwr_gear
    tprint("Gear %d" % (gear))

    if brake:
        eprint("Gear %d, Throttle %.2f, Braking" % (gear, throttle))
    else:
        eprint("Gear %d, Throttle %.2f" % (gear, throttle))
    write_file('gear.txt', gear)
    write_file('throttle.txt', float(throttle))

    # time.sleep(0.001)

eprint("CC Controller disconnected, Now Exit")
client_socket.close()
