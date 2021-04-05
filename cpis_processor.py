# import pandas as pd
import numpy as np


class CPIS_Processor:
    """
    Processor class.
    Only train() and test() are public functions.
    """
    def __init__(self, P_0=None, theta_0=None, directory=None):
        """
        Initialize the Processor class.
        Inputs:
            P_0: Initial P. See linear_regression_train function for details.
            theta_0: Initial theta. Defaults to the 0 array.
            directory: Directory to save the theta and P arrays.
        """
        if directory is None:
            self.directory = "./"
        else:
            self.directory = directory

        if P_0 is None:
            self.P = 100 * np.eye(3)
        else:
            self.P = P_0

        if theta_0 is None:
            self.theta = np.array([[0],[0],[0]])
        else:
            self.theta = theta_0

        np.savetxt(self.directory + "P.csv", self.P, delimiter=",")
        np.savetxt(self.directory + "theta.csv", self.theta, delimiter=",")

    def train(self, X_i, y_i, l=1):
        """
        Wrapper function for training the linear regression. Saves P and theta
        after each iteration.
        Inputs:
            X_i: Numpy column containing the current X variables.
            Y_i: Response variable
            l: Lambda. Forgetting factor. See linear_regression_train function
               for details.
        Returns updated theta and P.
        """
        self.theta, self.P = self.linear_regression_train(X_i, y_i, self.theta, self.P, l)
        np.savetxt(self.directory + "P.csv", self.P, delimiter=",")
        np.savetxt(self.directory + "theta.csv", self.theta, delimiter=",")
        return self.theta, self.P

    def linear_regression_train(self, X_i, y_i, theta, P, l):
        """
        Private function.
        Implements gradient descent algorithm for online linear regression.
        http://www.cs.tut.fi/~tabus/course/ASP/LectureNew10.pdf (Page 9)
        Inputs:
            X_i: Numpy column containing the current X variables.
            y_i: Response variable.
            theta: Current estimate of the predictors.
            P: Phi-inverse.
            l: Lambda. Forgetting factor.
        Returns updated theta.
        """
        pi = np.dot(X_i.T, P)
        gamma = l + np.dot(pi, X_i)
        k = pi.T / gamma
        alpha = y_i - np.dot(theta.T, X_i)
        theta = theta + alpha * k
        # print("k", k)
        P = 1 / l * (P - np.dot(k, pi))
        return theta, P

    def test(self, X_i, y_i, se_threshold):
        """
        Wrapper function for testing the linear regression. Retrieves most updated
        P and theta from csv.
        Inputs:
            X_i: Numpy column containing the current X variables.
            y_i: Response variable
            se_threshold: Squared error threshold. Must be greater than 0.
        Returns True if the current data point is not an anomaly else False.
        """
        theta = np.loadtxt(self.directory + "theta.csv", delimiter=",").reshape((3, 1))
        return self.linear_regression_test(X_i, y_i, theta)

    def linear_regression_test(self, X_i, y_i, theta):
        """
        Private function.
        Test if the current data point is not an anomaly.
        Inputs:
            X_i: Numpy column containing the current X variables.
            Y_i: Response variable
            se_threshold: Squared error threshold. Must be greater than 0.
        Returns True if the current data point is not an anomaly else False.
        """
        squared_error = (y_i - np.dot(X_i.T, theta)) ** 2
        # return True if squared_error <= se_threshold else False
        return squared_error

"""
def main():
    
    # Driver function.
    data = pd.read_csv("data.csv")
    data= data.drop(columns="Class")
    train_X = data.drop(columns=["Previous Speed"])
    train_Y = data['Current Speed'] - data['Previous Speed']
    processor = CPIS_Processor()
    for i in range(len(train_X)):
        X_i = train_X.iloc[i,].to_numpy().reshape((3,-1))
        y_i = train_Y.iloc[i,]
        processor.train(X_i, y_i)
"""

if __name__ == "__main__":
    main()



