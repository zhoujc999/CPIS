import socket
import sys
import select
import time
from math import pi
from time import sleep
import pidcontroller
from os import path
import fcntl

HOST = '0.0.0.0'
PORT = 53599

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', PORT))

server_socket.listen(5)
print("\n Listning on port: " + str(PORT))

client_socket, (client_ip, client_port) = server_socket.accept()
print("\n Client" + client_ip + "connected successfully\n")

throttle = 0.0
gear = 1
rpm = 0
while True:
    in_payload = client_socket.recv(104) # revist
    prefered_accel = in_payload.decode()
    prefered_accel = float(prefered_accel)
    # deserialize
    # payload = in_payload.split()
    # print(prefered_accel)
    
    # Read rpm from simulation
    with open('rpm.txt', 'r') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rpm = int(f.read())
        fcntl.flock(f, fcntl.LOCK_UN)

    # Engine control
    if prefered_accel > 1.0:
        throttle = 1.0
    elif prefered_accel < 0.0:
        throttle = 0.0
    else:
        throttle = prefered_accel
    mapping = [1100, 3000] # Shift down & shift up RPM
    if (throttle > 0.9):
        mapping = [4500, 7500]
    if rpm > mapping[1]:
        gear = min(5, gear+1)
    elif rpm < mapping[0]:
        gear = max(1, gear-1)
    
    print("Gear %d, Throttle %.2f" % (gear, throttle))
    with open('gear.txt', 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(gear))
        fcntl.flock(f, fcntl.LOCK_UN)
    with open('throttle.txt', 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(float(throttle)))
        fcntl.flock(f, fcntl.LOCK_UN)

    time.sleep(0.400)

print("Now Exit")
client_socket.close()