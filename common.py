import errno
import os
import socket
import sys
import select
import platform
import time
import pickle
import threading
import fcntl
import re

FORCE_TRAINING = False

# Main CPIS node
HOST = "100.0.0.1"
PORT = 53599
DATA_ALLKEYS = {
    "engine_ctrl": ["Throttle", "Gear", "RPM"],
    "cc_ctrl": ["Cur_Spd", "Set_Spd", "Pref_Accel"],
}

TR_ALLKEYS = {
    "engine_ctrl": [30, 45, 47, 49, 56, 58, 62, 63],
    "cc_ctrl": [44, 46, 53, 68],
}

ALLIPS = {
    "100.0.0.3": "cc_ctrl",
    "100.0.0.2": "engine_ctrl",
}

UPDATE_FREQ = 5.0
TRACE_COUNTER_SZ = 1000

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


""" Monitor guts """

def monitor_data_extract(line):
    res = re.match("_DATATRACE_ (.*) (\d+(?:\.\d+)?)", line)
    if not res:
        return None, None
    key = res.groups()[0]
    value = res.groups()[1]
    # eprint("Grep data: %s is %s" % (key, value))
    return key, value

def monitor_line_extract(line):
    res = re.match(".*.py\((\d+)\):.*", line)
    if not res:
        return -1
    line = res.groups()[0]
    return line

def monitor_guts(fifo, file_name, data_keys, trace_keys, pre_processor):
    eprint("Connecting to %s:%s ..." % (HOST, str(PORT)))
    connection_socket = connect_to_server_socket(HOST, PORT)
    eprint("Connected to %s:%s" % (HOST, str(PORT)))
    eprint("Opening FIFO pipe %s..." % fifo)
    fifo_fd = open(fifo)
    eprint("FIFO opened")

    buffer_lock = threading.Lock()
    data_buffer = []
    trace_counter_reduced_diff = []
    trace_counter_reduced = []
    trace_counter = [0] * TRACE_COUNTER_SZ
    main_counter = 0
    for _ in data_keys:
        data_buffer.append(-1.0)
    for _ in trace_keys:
        trace_counter_reduced_diff.append(0)
        trace_counter_reduced.append(0)

    # socket thread
    def socket_handler():
        while True:
            in_bytes = connection_socket.recv(1024)
            if len(in_bytes) == 0:
                break
            if (in_bytes == b'0'):
                continue
            # prepare data
            buffer_lock.acquire()
            data_buffer_copy = data_buffer.copy()
            for i in range(len(trace_keys)):
                trace_counter_reduced_diff[i] = trace_counter[trace_keys[i]] - trace_counter_reduced[i]
                trace_counter_reduced[i] = trace_counter[trace_keys[i]]
            buffer_lock.release()
            # pre-processing
            res = pre_processor(data_buffer_copy, trace_counter_reduced_diff)
            # send
            payload = pickle.dumps((data_buffer_copy, trace_counter_reduced_diff, res))
            connection_socket.send(payload)
            # eprint("Payload delivered\n")
            time.sleep(0.1)
            # eprint("RES=%d, %s" % (res, str(trace_counter_reduced_diff)))
    
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
        main_counter += 1
        if data[0] == '_':
            # Trace w/ Data
            key, value = monitor_data_extract(data)
            if not key:
                continue
            # eprint("[%d] Got %s=%s" % (main_counter, key, value))
            if key in data_keys:
                buffer_lock.acquire()
                data_buffer[data_keys.index(key)] = value
                buffer_lock.release()
        elif data.startswith(file_name):
            # Trace w/o Data
            line_num = int(monitor_line_extract(data))
            if line_num > 0 and line_num < TRACE_COUNTER_SZ:
                # eprint("line %d" % int(line_num))
                buffer_lock.acquire()
                trace_counter[line_num] += 1
                buffer_lock.release()

    eprint("PIPE Writer closed")
    fifo_fd.close()
    os._exit(2)


def read_file(name, type):
    line = ""
    retry_total = 5
    for i in range(retry_total):
        opened_file = open(name, 'r')
        fcntl.flock(opened_file, fcntl.LOCK_EX)
        line = opened_file.read()
        fcntl.flock(opened_file, fcntl.LOCK_UN)
        opened_file.close()
        if not line:
            eprint("Retry %d of %d" % (i, retry_total))
            time.sleep(0.01)
            continue
        value = type(line)
        return value
    raise ValueError("Unable to read %s: Got '%s'" % (name, line))


def write_file(name, value):
    with open(name, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(str(value))
        fcntl.flock(f, fcntl.LOCK_UN)

def watch_dog(input):
    watch_dog.violate_count = getattr(watch_dog, 'violate_count', 0)
    if input <= 0:
        watch_dog.violate_count += 1
        if (watch_dog.violate_count >= 3):
            return 1
    elif (watch_dog.violate_count > 1):
        watch_dog.violate_count -= 1 
    return 0

THROTTLE_SCALE = 2

def preferred_accel_to_accel(input):
    if input > THROTTLE_SCALE:
        return 1.0
    elif input < 0.0:
        return 0.0
    else:
        return (input / THROTTLE_SCALE)