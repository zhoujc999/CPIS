#!/usr/bin/python3

import socket
import sys
import select
import time
import pickle
from common import DATA_ALLKEYS, TR_ALLKEYS, ALLIPS, PORT, MON_ORDER, write_file
from common import FORCE_DATA_MODEL_TRAINING, FORCE_EXEC_MODEL_TRAINING, preferred_accel_to_accel
from cpis_processor import CPIS_Processor
import numpy as np
import os

import matplotlib.pyplot as plt

HOST = '0.0.0.0'
NUM_CLIENTS = len(ALLIPS)
CPIS_UPDATE_DLAY = 0.8

PLOT = True
colors = ["red","red", "orange", "green","blue", "purple"]
throt_rang = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
buffery = [0.0] * len(throt_rang)
buffery = np.array(buffery)
buffer_thrt = []
buffer_yi = []
buffer_color = []

def print_data_buffer(keys, data_buffer):
    for i in range(len(data_buffer)):
        print("%s=%s " % (keys[i], data_buffer[i]), end='')
    print(" ")

def main():
    file1 = open("new_data.txt", "a")
    should_train = True

    Threshold_alert = 5.0
    Threshold_alert_sqrt = np.sqrt(Threshold_alert)
    Threshold_calibrate = 1000 #2.0
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
    theta = None
    counters_invarts = None
    if not FORCE_EXEC_MODEL_TRAINING:
        counters_invarts = np.loadtxt("counters_invarts.txt", dtype=float)
    if not FORCE_DATA_MODEL_TRAINING:
        theta = np.loadtxt("theta.csv", delimiter=",").reshape((4, 1))
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
        keys[order] = DATA_ALLKEYS[client_name_l[order]]
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

    # Plot
    plt.axis([0, 1, -1, 10])

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
            import numpy.linalg as lalg
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

            # Mining invariants
            v = lalg.svd(matrix)[2]
            total_v = len(matrix)
            rules = []
            for null_vec in reversed(v):
                cur_res = np.abs(matrix.dot(null_vec))
                max_error = np.max(cur_res)
                disagree_count = np.count_nonzero(cur_res > 0.1)
                if (disagree_count == 0):
                    rules.append(null_vec)
                else:
                    break
            print("!Found %d Invariants, Next disagree ratio is %.2f, max error %.2f" %
                  (len(rules), disagree_count / total_v, max_error))
            np.savetxt("counters_invarts.txt", np.array(rules))

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
            write_file("alert_flag_exec.txt", 1)

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
            if (y_i < 20 and y_i > -20):
                # and cur_thrt != 0.0
                # and cur_thrt != 1.0):
                theta, P = LR_model.train(X_i, y_i, l=1)
                print("==Force Training." % theta)

                if PLOT:
                    """
                    plt.clf()
                    for plot_gear in [1,2,3,4,5]:
                        # plot_gear = int(cur_gear)
                        for i in range(0, len(throt_rang)):
                            plot_xi = np.array([cur_sped ** 2, (throt_rang[i] / plot_gear), cur_sped])
                            expected = LR_model.calc(plot_xi)
                            buffery[i] = expected
                        plt.plot(throt_rang, buffery, c=colors[plot_gear])
                    # plt.scatter(cur_thrt, y_i, c=colors[int(cur_gear)], s=80, edgecolors='none')
                    buffer_thrt.append(cur_thrt)
                    buffer_yi.append(y_i)
                    buffer_color.append(colors[int(cur_gear)])
                    plt.scatter(buffer_thrt, buffer_yi, c=buffer_color, s=80, edgecolors='none')
                    """
                    plt.scatter(cur_thrt, y_i, c=colors[int(cur_gear)], s=80, edgecolors='none')
                    plt.pause(0.05)

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
                    write_file("alert_flag_data.txt", 1)
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

        # Plot
        if PLOT:
            plt.clf()
            for plot_gear in [1,2,3,4,5]:
            # plot_gear = int(cur_gear)
                for i in range(0, len(throt_rang)):
                    plot_xi = np.array([cur_sped ** 2, (throt_rang[i] / plot_gear), cur_sped])
                    expected = LR_model.calc(plot_xi)
                    buffery[i] = expected
                plt.plot(throt_rang, buffery, c=colors[plot_gear])
                if (plot_gear == int(cur_gear)):
                    plt.fill_between(throt_rang, buffery - Threshold_alert_sqrt / 2,
                                     buffery + Threshold_alert_sqrt / 2, color=colors[plot_gear],alpha=0.1)
            # plt.plot(throt_rang, buffery, c=colors[plot_gear], linewidth=100, alpha=0.1)
            plt.scatter(cur_thrt, y_i, c=colors[int(cur_gear)], s=80, edgecolors='none')
            plt.xlabel("Throttle Input")
            plt.ylabel("Acceleration (km/(h*s))")
            plt.xlim([-0.1, 1.1])
            plt.ylim([-3, 20])
            plt.pause(0.05)

        time.sleep(CPIS_UPDATE_DLAY)
        print("")

    print("Now Exit")
    client_socket.close()

if __name__ == "__main__":
    main()