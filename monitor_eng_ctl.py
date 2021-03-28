#!/usr/bin/python3

from common import *

FIFO = 'pipe_eng_ctl'

def eng_ctl_pre_processor(data, counters):
    # Watch dog
    if watch_dog(counters[0]):
        eprint("Watch dog alert")
        return 1
    # serial
    if not (counters[0] == counters[-1] == counters[-2]):
        eprint("Serial exec not equal")
        return 1
    # branch
    if not (counters[0] == (counters[1] + counters[2] + counters[3])):
        eprint("Branch exec not equal")
        return 1
    return 0

monitor_init(FIFO)
monitor_guts(FIFO, "engine_ctrl.py",
             DATA_ALLKEYS["engine_ctrl"],
             TR_ALLKEYS["engine_ctrl"],
             eng_ctl_pre_processor)
