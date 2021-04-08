#!/usr/bin/python3

from common import *

FIFO = 'pipe_eng_ctl'

def eng_ctl_pre_processor(data, counters):
    # Watch dog
    if watch_dog(counters[0]):
        eprint("Watch dog alert")
        return 1
    # serial
    if assertion_counter(
        (counters[0] == counters[-1] == counters[-2]),
        threshold=5):
        eprint("Serial exec not equal")
        return 1
    # branch
    if assertion_counter(
        (counters[0] == (counters[1] + counters[2] + counters[3])),
        threshold=5):
        eprint("Branch exec not equal")
        return 1
    # RPM
    cur_rpm = int(data[2])
    if (cur_rpm > 15000 or cur_rpm < -1):
        eprint("Abnormal RPM")
        return 1
    # Gear
    cur_gear = int(data[1])
    if (cur_gear > 5 or cur_gear < 1):
        eprint("Abnormal Gear")
        return 1
    return 0

monitor_init(FIFO)
monitor_guts(FIFO, "engine_ctrl.py",
             DATA_ALLKEYS["engine_ctrl"],
             TR_ALLKEYS["engine_ctrl"],
             eng_ctl_pre_processor)
