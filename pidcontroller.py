import time

class PID:
    """PID controller.

    Modified from: https://github.com/korfuri/PIDController.git
    """

    def __init__(self, Kp, Ki, Kd, origin_time=None):
        if origin_time is None:
            origin_time = time.time()

        # Gains for each term
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        # Corrections (outputs)
        self.Cp = 0.0
        self.Ci = 0.0
        self.Cd = 0.0

        self.previous_time = origin_time
        self.previous_error = 0.0

    def Update(self, error, current_time=None, dt=None, ci_limit_L=None, ci_limit_H=None):
        if current_time is None:
            current_time = time.time()
        if not dt:
            dt = current_time - self.previous_time
        if dt <= 0.0:
            return 0
        de = error - self.previous_error

        self.Cp = error
        self.Ci += error * dt
        self.Cd = de / dt

        if (ci_limit_L is not None):
            self.Ci = max(self.Ci, ci_limit_L)
        if (ci_limit_H is not None):
            self.Ci = min(self.Ci, ci_limit_H)

        self.previous_time = current_time
        self.previous_error = error

        return (
            (self.Kp * self.Cp)    # proportional term
            + (self.Ki * self.Ci)  # integral term
            + (self.Kd * self.Cd)  # derivative term
        )