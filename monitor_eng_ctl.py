from common import *
import re

FIFO = 'pipe_eng_ctl'

def eng_ctl_filter(line):
    res = re.match("_DATATRACE_ (.*) (\d+(?:\.\d+)?)", line)
    if not res:
        return None, None
    key = res.groups()[0]
    value = res.groups()[1]
    # print("Grep data: %s is %s" % (key, value))
    return key, value
    

monitor_init(FIFO)
monitor_guts(FIFO, eng_ctl_filter)
