#!/usr/bin/python3

from common import *

FIFO = 'pipe_cc_ctl'

def cc_ctl_pre_processor(data, counters):
    # Watch dog
    if watch_dog(counters[0]):
        eprint("Watch dog alert")
        return 1
    # serial
    if assertion_counter(
        (counters[0] == counters[1] == counters[3]),
        threshold=5):
        eprint("Serial exec not equal")
        return 1
    # Speed Limit
    cur_spd = float(data[0])
    if (abs(cur_spd) > 300):
        eprint("Abnormal Speed")
        return 1
    # Set speed Limit
    cur_set_spd = float(data[1])
    if (abs(cur_set_spd) > 300):
        eprint("Abnormal Set Speed")
        return 1
    return 0

monitor_init(FIFO)
monitor_guts(FIFO, "cc_ctrl.py",
             DATA_ALLKEYS["cc_ctrl"],
             TR_ALLKEYS["cc_ctrl"],
             cc_ctl_pre_processor)
