import errno
import os
import socket
import sys
import select
import platform
import time
import pickle
import threading

# Main CPIS node
HOST = "100.0.0.1"
PORT = 53599
ALLKEYS = {
    "engine_ctrl": ["Throttle", "Gear", "RPM"],
    "cc_ctrl": ["Cur_Spd", "Set_Spd", "Pref_Accel"],
}

ALLIPS = {
    "100.0.0.3": "cc_ctrl",
    "100.0.0.2": "engine_ctrl",
}

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def tprint(*args, **kwargs):
    print("_DATATRACE_", *args, **kwargs)

def monitor_init(fifo):
    try:
        os.mkfifo(fifo)
    except OSError as oe: 
        if oe.errno != errno.EEXIST:
            raise

def connect_to_server_socket(host, port):
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while(1):
        try:
            connection_socket.connect((host, port))
        except ConnectionRefusedError:
            time.sleep(0.5)
            continue
        else:
            break
    return connection_socket


def monitor_guts(fifo, apply_filter, keys):
    eprint("Connecting to %s:%s ..." % (HOST, str(PORT)))
    connection_socket = connect_to_server_socket(HOST, PORT)
    eprint("Connected to %s:%s" % (HOST, str(PORT)))
    eprint("Opening FIFO pipe %s..." % fifo)
    fifo_fd = open(fifo)
    eprint("FIFO opened")

    buffer_lock = threading.Lock()
    buffer = []
    counter = 0
    for _ in keys:
        buffer.append(-1.0)

    # socket thread
    def socket_handler():
        while True:
            in_bytes = connection_socket.recv(1024)
            if len(in_bytes) == 0:
                break
            if (in_bytes == b'0'):
                continue
            buffer_lock.acquire()
            data=pickle.dumps(buffer)
            buffer_lock.release()
            # eprint("payload size is \n" + sys.getsizeof(payload_serialize))
            connection_socket.send(data)
            # eprint("Payload delivered\n")
            time.sleep(0.1)
        eprint("CPIS MAIN disconnected, now Exit")
        connection_socket.close()
        os._exit(1)
    thread = threading.Thread(target=socket_handler)
    thread.start()

    # Main thread & monitor pipe
    while True:
        data = fifo_fd.readline()
        if len(data) == 0:
            break
        counter += 1
        if data[0] != '_':
            continue
        key,value = apply_filter(data)
        if not key:
            continue
        eprint("[%d] Got %s=%s" % (counter, key, value))
        if key in keys:
            buffer_lock.acquire()
            buffer[keys.index(key)] = value
            buffer_lock.release()
    eprint("PIPE Writer closed")
    fifo_fd.close()
    os._exit(2)