import sys
import errno
import os

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

def monitor_guts(fifo, apply_filter):
    print("Opening FIFO %s..." % fifo)
    fifo_fd = open(fifo)
    print("FIFO opened")
    counter = 0
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
        print("[%d] Got %s=%s" % (counter, key, value))
    
    print("FIFO Writer closed")
    fifo_fd.close()