#!/usr/bin/python3

import socket
import sys
import select
import time
import pickle
from common import DATA_ALLKEYS, TR_ALLKEYS, ALLIPS, PORT
from common import FORCE_TRAINING
from cpis_processor import CPIS_Processor
import numpy as np
import os

HOST = '0.0.0.0'
NUM_CLIENTS = len(ALLIPS)
CPIS_UPDATE_DLAY = 0.8

client_socket_l = []
client_name_l = []
keys = []
data_buffer = []


def print_data_buffer():
    global spd_diff
    for i in range(len(data_buffer)):
        print("%s=%s " % (keys[i], data_buffer[i]), end='')
    print(" ")

def main():
    file1 = open("new_data.txt", "a")
    should_train = True

    Threshold_alert = 20.0
    Threshold_calibrate = 1.0
    Accu_alert = 0
    Accu_calibrate = 0
    Threshold_alert_accu = 3
    Threshold_calibrate_accu = 10
    Starting_delay = 10


    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))

    server_socket.listen(5)
    print("\n Listning on port: " + str(PORT))

#     Init the model
#     p0 = np.array([
# [2.210843984499893821e-06,-5.657178557028958886e-05,-3.752115930753636232e-05],
# [-5.657178557385380863e-05,5.305463786752321123e-03,8.656815972961321316e-04],
# [-3.752115931375383487e-05,8.656815972987671765e-04,6.564533706505748870e-04],
# ])
#     theta = np.array([
# [1.393763362373513586e-04],
# [8.894631089364557486e-02],
# [-5.111392825591626506e-03],
# ])
    theta = np.loadtxt("theta.csv", delimiter=",").reshape((4, 1))
    if FORCE_TRAINING:
        theta = None
    LR_model = CPIS_Processor(P_0=None, theta_0=theta, directory=None)

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
    prev_sped = 0.0
    spd_diff = 0.0
    prev_time = 0.0
    prev_gear = 1
    training_count = 0
    sped_idx = keys.index('Cur_Spd')
    gear_idx = keys.index('Gear')
    thrt_idx = keys.index('Throttle')
    while True:
        data_buffer.clear()
        if Starting_delay > 0:
            Starting_delay -= 1
            
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

        # Extract Data
        cur_sped = float(data_buffer[sped_idx])
        cur_thrt = float(data_buffer[thrt_idx])
        cur_gear = float(data_buffer[gear_idx])

        # Calc acceleration
        spd_diff = cur_sped - prev_sped
        prev_sped = cur_sped
        time_diff = time.time() - prev_time
        prev_time = time.time()

        # Features
        X_i = np.array([
            cur_sped,
            cur_thrt,
            cur_gear
        ])

        # More realistic Features
        X_i = np.array([
            cur_sped ** 2,
            (cur_thrt / cur_gear),
            cur_sped
        ])

        X_i = X_i.reshape((3, 1))
        y_i = spd_diff / time_diff
        # print("Xi=%s; yi=%s" % (X_i, y_i))

        # Force training
        if FORCE_TRAINING:
            if (y_i < 10 and y_i > -10):
                # and cur_thrt != 0.0
                # and cur_thrt != 1.0):
                theta, P = LR_model.train(X_i, y_i, l=1)
                print("==Force Training." % theta)

            time.sleep(CPIS_UPDATE_DLAY)
            continue
        

        # Online Train
        # training_count = 0
        if (training_count > 0 and
           cur_thrt != 0.0 and
           cur_thrt != 1.0):
                theta, P = LR_model.train(X_i, y_i, l=0.99)
                training_count -= 1
                should_train = False
                print("==Training." % theta)
        else:
            error = LR_model.test(X_i, y_i, None)[0][0]
            # should_train = True
            print("==Error is %s" % error)

            # Check for anomaly
            if error > Threshold_alert and Starting_delay == 0:
                Accu_alert += 1
                if (Accu_alert > Threshold_alert_accu or
                    error > 1000):
                    print("\nALERT\n")
                    Accu_alert = 0
            # Check for calibration
            elif error > Threshold_calibrate:
                Accu_calibrate += 1
                if Accu_calibrate > Threshold_calibrate_accu:
                    print("==Re-train for calibration")
                    Accu_calibrate = 0
                    training_count = 5
            else:
                Accu_alert = 0
                Accu_calibrate = 0

        time.sleep(CPIS_UPDATE_DLAY)

    print("Now Exit")
    client_socket.close()

if __name__ == "__main__":
    main()