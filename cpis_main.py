#!/usr/bin/python3

import socket
import sys
import select
import time
import pickle
from common import DATA_ALLKEYS, TR_ALLKEYS, ALLIPS, PORT

HOST = '0.0.0.0'
NUM_CLIENTS = len(ALLIPS)

client_socket_l = []
client_name_l = []
keys = []
data_buffer = []

def print_data_buffer():
    for i in range(len(data_buffer)):
        print("%s=%s " % (keys[i], data_buffer[i]), end='')
    print(" ")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))

    server_socket.listen(5)
    print("\n Listning on port: " + str(PORT))

    # Connect to CPIS monitors
    for i in range(NUM_CLIENTS):
        client_socket, (client_ip, client_port) = server_socket.accept()
        if client_ip not in ALLIPS:
            print("Unrecognized IP: %s" % client_ip)
            sys.exit(1)
        print("Client %d of %d %s(%s) connected successfully" %
            (i+1, NUM_CLIENTS, ALLIPS[client_ip], client_ip))

        client_socket_l.append(client_socket)
        client_name_l.append(ALLIPS[client_ip])
        keys.extend(DATA_ALLKEYS[client_name_l[i]])
    print("\n")

    # Receiving & processing monitors' data
    exit_now = False
    while True:
        data_buffer.clear()
        for i in range(NUM_CLIENTS):
            # Send
            client_socket_l[i].send(b'1')
            # Recv
            in_payload = client_socket_l[i].recv(1024)
            if len(in_payload) == 0:
                exit_now = True
            data, counters, res = pickle.loads(in_payload)
            data_buffer.extend(data)

            # Report from reprocessors
            if (res):
                print("!! Monitor [%s] reports anomaly !!" % client_name_l[i])

        if exit_now:
            break
        print_data_buffer()
        time.sleep(0.800)

    print("Now Exit")
    client_socket.close()

if __name__ == "__main__":
    main()