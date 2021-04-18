#!/usr/bin/python3

import socket
import sys
import select
import time
import pickle
from common import DATA_ALLKEYS, TR_ALLKEYS, ALLIPS, PORT, MON_ORDER
from common import FORCE_DATA_MODEL_TRAINING, FORCE_EXEC_MODEL_TRAINING, preferred_accel_to_accel
from cpis_processor import CPIS_Processor
import numpy as np
import os

HOST = '0.0.0.0'
NUM_CLIENTS = len(ALLIPS)
CPIS_UPDATE_DLAY = 0.8


def print_data_buffer(keys, data_buffer):
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

    Invar_threshold_alert = 1.0e-5
    Invar_threshold_alert_accu = 2
    Invar_accu = 0


    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))

    server_socket.listen(5)
    print("\n Listning on port: " + str(PORT))

    # Init the model
    theta = np.loadtxt("theta.csv", delimiter=",").reshape((4, 1))
    counters_invarts = np.loadtxt("counters_invarts.txt", dtype=float)
    if FORCE_DATA_MODEL_TRAINING:
        theta = None
    LR_model = CPIS_Processor(P_0=None, theta_0=theta, directory=None)

    # Connect to CPIS monitors
    keys = [None] * NUM_CLIENTS
    client_socket_l = [None] * NUM_CLIENTS
    client_name_l = [None] * NUM_CLIENTS
    for i in range(NUM_CLIENTS):
        client_socket, (client_ip, client_port) = server_socket.accept()
        if client_ip not in ALLIPS:
            print("Unrecognized IP: %s" % client_ip)
            sys.exit(1)
        print("Client %d of %d %s(%s) connected successfully" %
            (i+1, NUM_CLIENTS, ALLIPS[client_ip], client_ip))

        order = MON_ORDER.index(ALLIPS[client_ip])
        client_socket_l[order] = client_socket
        client_name_l[order] = ALLIPS[client_ip]
        keys[order] = DATA_ALLKEYS[client_name_l[i]]
    keys = [item for sublist in keys for item in sublist]
    print("Keys: ", keys)
    print("\n")
    

    # Receiving & processing monitors' data
    data_buffer = []
    exit_now = False
    prev_sped = 0.0
    spd_diff = 0.0
    prev_time = 0.0
    prev_gear = 1
    training_count = 0
    sped_idx = keys.index('Cur_Spd')
    gear_idx = keys.index('Gear')
    thrt_idx = keys.index('Throttle')
    pref_accel_idx = keys.index("Pref_Accel")

    # Processing exec trace counters
    counters_matrix = []
    counters_buffer = []
    counters_matrix_stat = None

    while True:
        data_buffer.clear()
        counters_buffer.clear()
        if Starting_delay > 0:
            Starting_delay -= 1
            
        for i in range(NUM_CLIENTS):
            # Send
            client_socket_l[i].send(b'1')
            # Recv
            in_payload = client_socket_l[i].recv(1024)
            if len(in_payload) == 0:
                exit_now = True
                break
            data, counters, res = pickle.loads(in_payload)
            data_buffer.extend(data)
            counters_buffer.extend(counters)
            # Report from reprocessors
            if (res):
                print("\n!! Monitor [%s] reports anomaly !!\n" % client_name_l[i])

        if exit_now:
            break
        print_data_buffer(keys, data_buffer)

        # Extract Data
        cur_sped = float(data_buffer[sped_idx])
        cur_thrt = float(data_buffer[thrt_idx])
        cur_gear = float(data_buffer[gear_idx])
        cur_thrt_from_cc = preferred_accel_to_accel(float(data_buffer[pref_accel_idx]))

        """ ======================== Exec Invariants Model =================== """
        if FORCE_EXEC_MODEL_TRAINING:
            import random
            print("\nNew Counters [%s]" % counters_buffer)
            if counters_matrix_stat is None:
                counters_matrix_stat = np.array(counters_buffer)
            else:
                counters_matrix_stat += np.array(counters_buffer)
            code_cov = np.count_nonzero(counters_matrix_stat) / len(counters_buffer)
            print("Code coverage: %.2f" % (code_cov * 100))
            counters_matrix.append(counters_buffer.copy())
            matrix = np.array(counters_matrix, dtype=int)
            # print(matrix)
            np.savetxt("counters_mtx.txt", matrix)
            time.sleep(random.uniform(2, 4))
            continue

        # Check invariants
        counters_input = np.array(counters_buffer)
        res = np.dot(counters_invarts, counters_input)
        error = np.max(np.abs(res))
        if (error > Invar_threshold_alert):
            Invar_accu += 1
        else:
            Invar_accu = 0
        if (Invar_accu > Invar_threshold_alert_accu):
            print("\n!! Exec Invariants Anomaly !!\n")

        print("== Exec Invariants Error %.3f" % error)

        """ ======================== Linear Regression Model =================== """
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
        cur_thrt = cur_thrt_from_cc
        X_i = np.array([
            cur_sped ** 2,
            (cur_thrt / cur_gear),
            cur_sped
        ])

        X_i = X_i.reshape((3, 1))
        y_i = spd_diff / time_diff
        # print("Xi=%s; yi=%s" % (X_i, y_i))

        # Force training
        if FORCE_DATA_MODEL_TRAINING:
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
            print("== Data Model Error %.3f" % error)

            # Check for anomaly
            if error > Threshold_alert and Starting_delay == 0:
                Accu_alert += 1
                if (Accu_alert > Threshold_alert_accu or
                    error > 1000):
                    print("\n!! Accel Model Anomaly !!\n")
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
        print("")

    print("Now Exit")
    client_socket.close()

if __name__ == "__main__":
    main()