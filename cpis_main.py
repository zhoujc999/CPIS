#!/usr/bin/python3

import socket
import sys
import select
import time
import pickle

HOST = '0.0.0.0'
PORT = 53599
NUM_CLIENTS = 1

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('', PORT))

server_socket.listen(5)
print("\n Listning on port: " + str(PORT))

client_socket_l = []
client_ip_l = []

for i in range(NUM_CLIENTS):
	client_socket, (client_ip, client_port) = server_socket.accept()
	print("\n Client %d of %d (%s) connected successfully" %
	      (i+1, NUM_CLIENTS, client_ip))
	client_socket_l.append(client_socket)
	client_ip_l.append(client_ip)

buffer = []
exit_now = False
while True:
	buffer.clear()
	for i in range(NUM_CLIENTS):
		# Send
		client_socket_l[i].send(b'1')
		# Recv
		in_payload = client_socket_l[i].recv(1024)
		if len(in_payload) == 0:
			exit_now = True
		buffer.append(pickle.loads(in_payload))

	# deserialize
	# payload = in_payload.split()
	if exit_now:
		break
	print(buffer)
	time.sleep(0.800)

print("Now Exit")
client_socket.close()
