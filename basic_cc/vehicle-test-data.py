
import numpy as np
import matplotlib.pyplot as plt
from math import pi
from time import sleep
import pidcontroller
from os import path
import pandas as pd

def motor_torque(omega, params={}):
    # Set up the system parameters
    Tm = params.get('Tm', 190.)             # engine torque constant
    omega_m = params.get('omega_m', 420.)   # peak engine angular speed
    beta = params.get('beta', 0.4)          # peak engine rolloff

    return np.clip(Tm * (1 - beta * (omega/omega_m - 1)**2), 0, None)

def vehicle_update(t, x, u, params={}):
    """Vehicle dynamics for cruise control system.

    Modified from https://github.com/python-control/python-control.git

    Parameters
    ----------
    x : array
         System state: car velocity in m/s
    u : array
         System input: [throttle, gear, road_slope], where throttle is
         a float between 0 and 1, gear is an integer between 1 and 5,
         and road_slope is in rad.

    Returns
    -------
    float
        Vehicle acceleration

    """
    from math import copysign, sin
    sign = lambda x: copysign(1, x)         # define the sign() function

    # Set up the system parameters
    m = params.get('m', 1600.)              # vehicle mass, kg
    g = params.get('g', 9.8)                # gravitational constant, m/s^2
    Cr = params.get('Cr', 0.01)             # coefficient of rolling friction
    Cd = params.get('Cd', 0.32)             # drag coefficient
    rho = params.get('rho', 1.3)            # density of air, kg/m^3
    A = params.get('A', 2.4)                # car area, m^2
    alpha = params.get(
        'alpha', [40, 25, 16, 12, 10])      # gear ratio / wheel radius

    # Define variables for vehicle state and inputs
    v = x[0]                           # vehicle velocity
    throttle = np.clip(u[0], 0, 1)     # vehicle throttle
    gear = u[1]                        # vehicle gear
    theta = u[2]                       # road slope

    # Force generated by the engine

    omega = alpha[int(gear)-1] * v      # engine angular speed
    F = alpha[int(gear)-1] * motor_torque(omega, params) * throttle

    # Disturbance forces
    #
    # The disturbance force Fd has three major components: Fg, the forces due
    # to gravity; Fr, the forces due to rolling friction; and Fa, the
    # aerodynamic drag.

    # Letting the slope of the road be \theta (theta), gravity gives the
    # force Fg = m g sin \theta.

    Fg = m * g * sin(theta)

    # A simple model of rolling friction is Fr = m g Cr sgn(v), where Cr is
    # the coefficient of rolling friction and sgn(v) is the sign of v (±1) or
    # zero if v = 0.

    Fr  = m * g * Cr * sign(v)

    # The aerodynamic drag is proportional to the square of the speed: Fa =
    # 1/2 \rho Cd A |v| v, where \rho is the density of air, Cd is the
    # shape-dependent aerodynamic drag coefficient, and A is the frontal area
    # of the car.

    Fa = 1/2 * rho * Cd * A * abs(v) * v

    # Final acceleration on the car
    Fd = Fg + Fr + Fa
    dv = (F - Fd) / m

    return dv, omega

def main():
    print("!!!")
    set_speed = 15
    cur_speed = 0.0
    dv = 0.0
    omega = 0.0
    pid = pidcontroller.PID(1, 0.1, 1)
    gear = 1

    curr_speeds = []
    prev_speeds = []
    throttles = []
    gears = []

    df = None
    if not path.exists("data.csv"):
        df = pd.DataFrame(columns=["Current Speed", "Previous Speed", "Throttle", "Gear", "Class"])
    else:
        df = pd.read_csv("data.csv")


    # Init file
    if not path.exists("set_speed.txt"):
        with open('set_speed.txt', 'w') as f:
            f.write("50")


    my_class = 1
    # good = 0

    for i in range(4000):
        # Cruise control
        with open('set_speed.txt', 'r') as opened_file:
            set_speed = int(opened_file.read()) / 3.6
        diff = set_speed - cur_speed
        """
        if diff > 0:
            throttle = min(diff / 10, 0.8)
        """
        spd_control = pid.Update(diff, dt=10, ci_limit_L=-10, ci_limit_H=200) / 20

        # Engine control
        if spd_control > 1.0:
            throttle = 1.0
        elif spd_control < 0.0:
            throttle = 0.0
        else:
            throttle = spd_control
        mapping = [1100, 3000] # Shift down & shift up RPM
        if (throttle > 0.9):
            mapping = [4500, 7500]
        rpm = omega / ((2*pi)/60)
        if rpm > mapping[1]:
            gear = min(5, gear+1)
        elif rpm < mapping[0]:
            gear = max(1, gear-1)

        # Vehicle simulation
        dv, omega = vehicle_update(0, [cur_speed], [throttle, gear, 0])
        new_speed = cur_speed + (dv * 0.1)

        df = df.append({"Current Speed": new_speed * 3.6, "Previous Speed": cur_speed * 3.6, "Throttle": throttle, "Gear": gear, "Class": my_class}, ignore_index=True)
        cur_speed = new_speed



        print("Speed %d KMH, RPM %d, Gear %d, Throttle %.2f" %
              (cur_speed * 3.6, rpm, gear, throttle))
        sleep(0.1)

    df.to_csv("data.csv")

if __name__ == '__main__':
    main()